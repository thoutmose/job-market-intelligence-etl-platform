from airflow.sdk import dag, task
from airflow.utils.edgemodifier import Label
from pendulum import datetime
from airflow.sdk.bases.sensor import PokeReturnValue
from airflow.sdk.bases.hook import BaseHook

@dag(
    dag_id="job_post_dag",
    start_date=datetime(2026, 1, 1, tz="Europe/Paris"),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    max_consecutive_failed_dag_runs=3,
    tags=["job_post", "daily"],
    description="A DAG to extract, transform, and load job postings data.",
)
def job_post_dag():
    """
    Docstring
    """

    @task.sensor(poke_interval=60, timeout=600, mode="poke")
    def is_api_available() -> PokeReturnValue:
        import requests

        api = BaseHook.get_connection("jsearch_api")
        endpoint_path = api.extra_dejson.get("endpoint")
        key = api.extra_dejson.get("key")
        num_page = api.extra_dejson.get("num_page")
        country = api.extra_dejson.get("country")
        date = api.extra_dejson.get("posted_at")
        
        base_url = f"{api.host}/{endpoint_path}"
        title = "data%20engineer"
        query_params = f"?query={title}"
        filter = f"&num_pages={num_page}&country={country}&date_posted={date}"
        url = base_url + query_params + filter
        print(f"Checking API availability at {url}")

        headers = {"x-api-key": key}

        response = requests.get(url, headers=headers)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API returned error: {response.text}")
            return PokeReturnValue(is_done=False, xcom_value=url)
        
        response_json = response.json()
        condition = "data" in response_json and len(response_json["data"]) > 0
        return PokeReturnValue(is_done=condition, xcom_value=url)

    @task
    def extract(url):
        import requests
        
        api = BaseHook.get_connection("jsearch_api")
        key = api.extra_dejson.get("key")
        headers = {"x-api-key": key}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        jobs_data = response.json().get("data", [])
        
        extracted_jobs = []
        for job in jobs_data:
            apply_options = job.get("apply_options", [])
            publisher = apply_options[0].get("publisher") if apply_options else job.get("job_publisher")
            apply_link = apply_options[0].get("apply_link") if apply_options else job.get("job_apply_link")
            
            extracted_job = {
                "job_id": job.get("job_id"),
                "job_city": job.get("job_city"),
                "job_title": job.get("job_title"),
                "job_salary": job.get("job_salary"),
                "job_country": job.get("job_country"),
                "job_benefits": job.get("job_benefits"),
                "job_location": job.get("job_location"),
                "publisher": publisher,
                "apply_link": apply_link,
                "employer_name": job.get("employer_name"),
                "job_apply_link": job.get("job_apply_link"),
                "job_max_salary": job.get("job_max_salary"),
                "job_min_salary": job.get("job_min_salary"),
                "job_description": job.get("job_description"),
                "job_employment_type": job.get("job_employment_type"),
                "job_posted_at_timestamp": job.get("job_posted_at_timestamp"),
            }
            extracted_jobs.append(extracted_job)
        
        print(f"Extracted {len(extracted_jobs)} job postings")
        return extracted_jobs

    @task
    def transform(data):
        import json
        import re
        import csv
        from pathlib import Path

        # hard skills
        root = Path(__file__).parent.parent
        mad_landscape_file_path = root / "data" / "mad_landscape.json"
        tech_file_path = root / "data" / "technologies.json"
        post_code_insee_file_path = root / "data" / "post_code_insee.csv"
        
        with open(mad_landscape_file_path, "r") as f:
            mad_landscape = json.load(f)

        with open(tech_file_path, "r") as f:
            technologies = json.load(f)
        
        # Load postal code lookup table
        postal_code_lookup = {}
        with open(post_code_insee_file_path, "r", encoding="latin-1") as f:
            csv_reader = csv.DictReader(f, delimiter=";")
            for row in csv_reader:
                city_name = row.get("Nom_de_la_commune", "").strip().upper()
                postal_code = row.get("Code_postal", "").strip()
                if city_name and postal_code:
                    # Store the first postal code found for each city
                    if city_name not in postal_code_lookup:
                        postal_code_lookup[city_name] = postal_code

        # Process ALL jobs, not just the first one
        for job in data:
            # Uppercase job_city and lookup postal code
            job_city = job.get("job_city", "")
            if job_city:
                job_city_upper = job_city.upper()
                job["job_city"] = job_city_upper
                
                # Lookup postal code
                postal_code = postal_code_lookup.get(job_city_upper)
                if postal_code:
                    job["postal_code"] = postal_code
                    # Create ISO 3166-2:FR region code (FR-XX) from first two digits
                    if len(postal_code) >= 2:
                        department_code = postal_code[:2]
                        job["iso_region_code"] = f"FR-{department_code}"
                    else:
                        job["iso_region_code"] = None
                else:
                    job["postal_code"] = None
                    job["iso_region_code"] = None
            else:
                job["postal_code"] = None
                job["iso_region_code"] = None
            
            description = job.get("job_description", "").lower()
            found_technologies = set()
            
            for category, tools in mad_landscape.items():
                for tech in tools:
                    pattern = r'\b' + re.escape(tech.lower()) + r'\b'
                    if re.search(pattern, description):
                        found_technologies.add(tech)
            
            for tech in technologies:
                pattern = r'\b' + re.escape(tech.lower()) + r'\b'
                if re.search(pattern, description):
                    found_technologies.add(tech)
            
            # remove duplicates by converting to set
            technologies_list = list(set(found_technologies))
            
            # seniority level extraction (simple keyword matching)
            seniority_levels = ["junior", "confirmé", "sénior", "lead", "manager"]
            years_of_experience = r"(\d+)\+?\s*(an[née]{0,3}s|years?)"
            seniority_found = []
            for level in seniority_levels:
                pattern = r'\b' + re.escape(level.lower()) + r'\b'
                if re.search(pattern, description):
                    seniority_found.append(level)
            experience_match = re.search(years_of_experience, description)
            if experience_match:
                seniority_found.append(experience_match.group(0))

            # salary
            salary_pattern = r'(\d{2,3}(?:[ ,.\u00A0]\d{3})*(?:[ ,.\u00A0]\d{3})?)(?:\s*€|\s*euros?)'
            salary_matches = re.findall(salary_pattern, description)
            salaries_found = []
            for match in salary_matches:
                salary_str = match.replace(" ", "").replace("\u00A0", "").replace(",", "").replace(".", "")
                try:
                    salary_value = int(salary_str)
                    salaries_found.append(salary_value)
                except ValueError:
                    continue
            
            # benefits
            remote_work_keywords = ["remote", "télétravail", "hybride", "full remote", "100% remote"]
            misc_benefits_keywords = [
                ("cse", r"\bcse\b"),
                ("tickets restaurant", r"\btickets?\-?\s?restaurant\b"),
                ("assurance santé", r"\bassurance\s+santé\b"),
                ("mutuelle", r"\bmutuelle\b"),
                ("rtt", r"\brtt\b"),
                ("prime", r"\bprimes?\b"),
                ("intéressement", r"\bintéressement\b"),
                ("participation", r"\bparticipation\b"),
                ("13ème mois", r"\b13[èe]?me?\s+mois\b"),
            ]
            benefits_found = []
            for keyword in remote_work_keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, description):
                    benefits_found.append(keyword)

            for benefit_name, pattern in misc_benefits_keywords:
                if re.search(pattern, description, re.IGNORECASE):
                    benefits_found.append(benefit_name) 

            # Add extracted data to this specific job
            job["hard_skills"] = technologies_list
            job["seniority_levels"] = seniority_found
            job["salaries_mentioned"] = salaries_found
            job["benefits_mentioned"] = benefits_found

        print(f"Transformed {len(data)} jobs")
        # remove fields
        remove_fields = [
            "job_country",
            "job_location",
            "job_description",
            "job_apply_link",
        ]
        for job in data:
            for field in remove_fields:
                job.pop(field, None)
        return data

    @task
    def load(data):
        import json
        import psycopg2
        from datetime import datetime
        
        # Get PostgreSQL connection from Airflow
        db_conn = BaseHook.get_connection("postgres_job_db")
        
        conn = psycopg2.connect(
            host=db_conn.host,
            port=db_conn.port or 5432,
            database=db_conn.schema,
            user=db_conn.login,
            password=db_conn.password
        )
        
        cursor = conn.cursor()
        
        try:
            for job in data:
                # Extract job timestamp and convert to date
                timestamp = job.get("job_posted_at_timestamp")
                if timestamp:
                    posted_date = datetime.fromtimestamp(timestamp)
                else:
                    posted_date = datetime.now()
                
                # === INSERT/GET dim_date ===
                date_key = int(posted_date.strftime("%Y%m%d"))
                cursor.execute("""
                    INSERT INTO dim_date (
                        date_key, full_date, year, quarter, month, month_name,
                        day, day_of_week, day_name, week_of_year, is_weekend
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (date_key) DO NOTHING
                """, (
                    date_key,
                    posted_date.date(),
                    posted_date.year,
                    (posted_date.month - 1) // 3 + 1,
                    posted_date.month,
                    posted_date.strftime("%B"),
                    posted_date.day,
                    posted_date.weekday(),
                    posted_date.strftime("%A"),
                    posted_date.isocalendar()[1],
                    posted_date.weekday() >= 5
                ))
                
                # === INSERT/GET dim_location ===
                job_city = job.get("job_city") or "Unknown"
                job_country = job.get("job_country") or "Unknown"
                postal_code = job.get("postal_code")
                iso_region_code = job.get("iso_region_code")
                
                cursor.execute("""
                    SELECT location_key FROM dim_location 
                    WHERE job_city = %s AND job_country = %s
                """, (job_city, job_country))
                
                result = cursor.fetchone()
                if result:
                    location_key = result[0]
                    # Update postcode and isocode3166 if they were found
                    if postal_code or iso_region_code:
                        cursor.execute("""
                            UPDATE dim_location 
                            SET postcode = COALESCE(%s, postcode),
                                isocode3166 = COALESCE(%s, isocode3166)
                            WHERE location_key = %s
                        """, (postal_code, iso_region_code, location_key))
                else:
                    # Generate new location_key
                    cursor.execute("SELECT COALESCE(MAX(location_key), 0) + 1 FROM dim_location")
                    location_key = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        INSERT INTO dim_location (
                            location_key, job_city, job_country, job_region, 
                            continent, latitude, longitude, postcode, isocode3166
                        ) VALUES (
                            %s, %s, %s, NULL, NULL, NULL, NULL, %s, %s
                        )
                    """, (location_key, job_city, job_country, postal_code, iso_region_code))
                
                # === INSERT/GET dim_employer ===
                employer_name = job.get("employer_name") or "Unknown"
                publisher = job.get("publisher")
                
                cursor.execute("""
                    SELECT employer_key FROM dim_employer 
                    WHERE employer_name = %s
                """, (employer_name,))
                
                result = cursor.fetchone()
                if result:
                    employer_key = result[0]
                else:
                    # Generate new employer_key
                    cursor.execute("SELECT COALESCE(MAX(employer_key), 0) + 1 FROM dim_employer")
                    employer_key = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        INSERT INTO dim_employer (
                            employer_key, employer_name, publisher, 
                            industry, company_size, founded_year
                        ) VALUES (
                            %s, %s, %s, NULL, NULL, NULL
                        )
                    """, (employer_key, employer_name, publisher))
                
                # === INSERT fact_job_post ===
                # Convert lists to comma-separated strings
                technologies = job.get("hard_skills", [])
                benefits = job.get("benefits_mentioned", [])
                seniority = job.get("seniority_levels", [])
                
                technologies_str = ",".join(technologies) if technologies else None
                benefits_str = ",".join(benefits) if benefits else None
                seniority_str = ",".join(seniority) if seniority else None
                
                # Generate job_key from job_id hash
                job_key = hash(job.get("job_id")) & 0x7FFFFFFFFFFFFFFF  # Positive 64-bit int
                
                cursor.execute("""
                    INSERT INTO fact_job_post (
                        job_key, date_key, location_key, employer_key,
                        job_id, job_title, apply_link, employment_type,
                        posted_timestamp, job_salary, job_min_salary, job_max_salary,
                        technologies_list, tools_list, benefits_list, seniority_levels_list,
                        technology_count, tools_count, benefits_count
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (job_id) DO UPDATE SET
                        job_title = EXCLUDED.job_title,
                        technologies_list = EXCLUDED.technologies_list,
                        benefits_list = EXCLUDED.benefits_list,
                        seniority_levels_list = EXCLUDED.seniority_levels_list,
                        technology_count = EXCLUDED.technology_count,
                        benefits_count = EXCLUDED.benefits_count
                """, (
                    job_key,
                    date_key,
                    location_key,
                    employer_key,
                    job.get("job_id"),
                    job.get("job_title"),
                    job.get("apply_link"),
                    job.get("job_employment_type"),
                    timestamp,
                    job.get("job_salary"),
                    job.get("job_min_salary"),
                    job.get("job_max_salary"),
                    technologies_str,
                    technologies_str,  # tools_list (same as technologies for now)
                    benefits_str,
                    seniority_str,
                    len(technologies),
                    len(technologies),
                    len(benefits)
                ))
            
            conn.commit()
            print(f"Successfully loaded {len(data)} job postings to database")
            
        except Exception as e:
            conn.rollback()
            print(f"Error loading data: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        return {"status": "loaded", "count": len(data)}

    # Define task dependencies, order of execution
    is_api_available_task = is_api_available()
    extracted_data = extract(is_api_available_task)
    transformed_data = transform(extracted_data)
    load_data = load(transformed_data)

    is_api_available_task >> Label("API is available") >> extracted_data
    extracted_data >> Label("extraction complete") >> transformed_data
    transformed_data >> Label("transformation complete") >> load_data


# Dag Declaration
job_post_dag()