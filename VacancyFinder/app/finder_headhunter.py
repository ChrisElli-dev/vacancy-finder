import requests
import os
import psycopg2

class finder_headhunter:
    def __init__(self):
        self.db_conn = psycopg2.connect(
            host=os.getenv('DATA_HOST'),
            port=os.getenv('DATA_PORT'),
            database=os.getenv('DATA_NAME'),
            user=os.getenv('DATA_USER'),
            password=os.getenv('DATA_PASSWORD')
        )

    def get_vacancies(self, query, salary=None, location=None):
        url = "https://api.hh.ru/vacancies"
        params = {
            "text": query,
            "salary": salary,
            "area": location
        }
        response = requests.get(url, params=params)
        return response.json()

    def save_to_db(self, positions):
        cursor = self.db_conn.cursor()
        for position in positions.get('items', []):
            expertise = ', '.join(skill['name'] for skill in position.get('key_skills', []))
            type_of_employment = position.get('employment', {}).get('name', '')
            wage = position.get('salary')
            wage_from = wage.get('from') if wage else None
            cursor.execute(
                """
                INSERT INTO positions (name, expertise, type_of_employment, wage, updated_on)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    expertise = EXCLUDED.expertise,
                    type_of_employment = EXCLUDED.type_of_employment,
                    wage = EXCLUDED.wage,
                    updated_on = now();
                """,
                (position['name'], expertise, type_of_employment, wage_from)
            )
        self.db_conn.commit()
        cursor.close()

    def parse_and_save(self, search_term, expected_wage=None, region=None):
        positions = self.get_vacancies(search_term, expected_wage, region)
        self.save_to_db(positions)
