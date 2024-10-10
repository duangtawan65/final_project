import pandas as pd
from django.core.management.base import BaseCommand
from healmind.models import Questionnaire, Question, Choice, Result

class Command(BaseCommand):
    help = 'Load data from an Excel file into the database'

    def handle(self, *args, **kwargs):
        # Load the Excel data
        file_path = 'C:/Users/Asus/PycharmProjects/final_project/finalproject/healmind/excel_files/questionnaire_data.xlsx'
        excel_data = pd.read_excel(file_path, sheet_name=None)

        # Extract the data from each sheet
        questionnaire_data = excel_data['Questionnaire']
        question_data = excel_data['Question']
        choice_data = excel_data['Choice']
        result_data = excel_data['Result']

        # Insert the data into the database
        for _, row in questionnaire_data.iterrows():
            Questionnaire.objects.get_or_create(
                id=row['Questionnaire_ID'],  # Set ID only if it's necessary
                defaults={
                    'questionnaire_name': row['Questionnaire_Name'],  # Correct field name for the model
                    'description': row['Description']
                }
            )

        for _, row in question_data.iterrows():
            questionnaire = Questionnaire.objects.get(id=row['Questionnaire_ID'])
            Question.objects.get_or_create(
                id=row['Question_ID'],  # Explicitly setting the Question ID if necessary
                defaults={
                    'questionnaire': questionnaire,  # Foreign key relationship
                    'question_content': row['Question_content']  # Correct field name for question content
                }
            )

        for _, row in choice_data.iterrows():
            question = Question.objects.get(id=row['Question_ID'])
            Choice.objects.get_or_create(
                id=row['Response_ID'],  # Explicitly setting the Response ID if necessary
                defaults={
                    'question': question,  # Foreign key relationship
                    'response_value': row['Response_Value'],  # Correct field name
                    'response_text': row['Response_Text']  # Correct field name
                }
            )

        for _, row in result_data.iterrows():
            questionnaire = Questionnaire.objects.get(id=row['Questionnaire_ID'])
            Result.objects.get_or_create(
                id=row['Result_ID'],  # Explicitly setting the Result ID if necessary
                defaults={
                    'questionnaire': questionnaire,  # Foreign key relationship
                    'score_low': row['Score_Low'],  # Correct field name
                    'score_high': row['Score_High'],  # Correct field name
                    'stress_level': row['Stress_Level'],  # Correct field name
                    'result_description': row['Result_Description']  # Correct field name
                }
            )

        # Print success message
        self.stdout.write(self.style.SUCCESS('Data successfully loaded into the database'))
