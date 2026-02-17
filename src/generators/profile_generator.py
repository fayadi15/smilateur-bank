import uuid
import random
import pandas as pd
from typing import List, Dict, Any
from faker import Faker
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ProfileGenerator:
    """
    Generates synthetic profiles for credit eligibility testing in Tunisia.
    """
    
    def __init__(self, locale: str = 'fr_FR'):
        self.fake = Faker(locale)
        # Seed for reproducibility if needed, but keeping it random for now
        
    def generate_single_profile(self) -> Dict[str, Any]:
        """
        Generates a single profile dictionary with Tunisian context.
        """
        # Job status specific to Tunisia context
        job_statuses = ['Fonctionnaire', 'Secteur Privé', 'Profession Libérale', 'Commerçant', 'Retraité']
        # Weights for job status (approximation)
        job_weights = [0.35, 0.45, 0.10, 0.05, 0.05]
        
        status = random.choices(job_statuses, weights=job_weights, k=1)[0]
        
        # Salary logic based on status (TND)
        if status == 'Fonctionnaire':
            salary = random.randint(800, 3500)
        elif status == 'Secteur Privé':
            salary = random.randint(500, 4000)
        elif status == 'Profession Libérale':
            salary = random.randint(1500, 8000) # Can be higher
        elif status == 'Retraité':
             salary = random.randint(400, 2500)
        else: # Commerçant / Autre
            salary = random.randint(300, 5000)

        age = random.randint(21, 65) # Banks usually require 21+
        
        # Loan Types logic
        loan_types = ['AUTO', 'IMMO', 'CONSO', 'VOYAGE']
        loan_type = random.choices(loan_types, weights=[0.4, 0.3, 0.2, 0.1], k=1)[0]
        
        if loan_type == 'AUTO':
            loan_amount = random.randint(15, 80) * 1000
            duration = random.choice([24, 36, 48, 60, 72, 84])
        elif loan_type == 'IMMO':
            loan_amount = random.randint(80, 500) * 1000
            duration = random.choice([120, 180, 240, 300]) # Up to 25 years
        elif loan_type == 'CONSO':
            loan_amount = random.randint(2, 25) * 1000
            duration = random.choice([12, 24, 36, 48, 60])
        else: # VOYAGE
            loan_amount = random.randint(1, 10) * 1000
            duration = random.choice([6, 12, 18, 24])

        # Adjust loan amount based on salary (simple heuristic for realism)
        # For IMMO, we allow much higher multiple of salary
        if loan_type == 'IMMO':
            max_loan_capacity = salary * 0.4 * duration
        else:
            max_loan_capacity = salary * 0.4 * 60 # Roughly 40% debt ratio over 5 years
            
        if loan_amount > max_loan_capacity * 1.5:
             loan_amount = int(max_loan_capacity * random.uniform(0.7, 1.0))
        
        # Ensure minimums
        if loan_amount < 1000: loan_amount = 1000

        profile = {
            "id": str(uuid.uuid4()),
            "age": age,
            "salaire_net": salary,
            "statut_pro": status,
            "anciennete": random.randint(0, 20), # Years
            "situation_famille": random.choice(['Célibataire', 'Marié', 'Divorcé', 'Veuf']),
            "nombre_enfants": random.choices([0, 1, 2, 3, 4], weights=[0.4, 0.2, 0.2, 0.1, 0.1])[0],
            "autres_credits": random.choice([0, 0, 0, random.randint(100, 800)]), # ~25% have other credits
            "montant_pret_demande": int(loan_amount),
            "duree_mois": duration,
            "loan_type": loan_type
        }
        return profile

    def generate_profiles(self, count: int = 1000, output_csv: str = None) -> List[Dict[str, Any]]:
        """
        Generates a list of profiles and optionally saves to CSV.
        """
        logger.info(f"Generating {count} profiles...")
        profiles = [self.generate_single_profile() for _ in range(count)]
        
        if output_csv:
            df = pd.DataFrame(profiles)
            df.to_csv(output_csv, index=False)
            logger.info(f"Profiles saved to {output_csv}")
            
        return profiles

if __name__ == "__main__":
    # Test execution
    gen = ProfileGenerator()
    gen.generate_profiles(10, "data/test_profiles.csv")
