import os.path
from django.contrib.auth.models import User
import pandas as pd
from django.core.management.base import BaseCommand
from healmind.models import *
from openpyxl import load_workbook
from django.conf import settings
from django.core.exceptions import ValidationError



class Command(BaseCommand):
    help = 'Load data from an Excel file into the database'

    def handle(self, *args, **kwargs):
        # Load the Excel data
        file_path = os.path.join(settings.BASE_DIR,'healmind/fixtures/data1.xlsx')
        excel_data = pd.read_excel(file_path, sheet_name=None)

        # Load Excel workbook
        wb = load_workbook(filename=file_path)
        ws = wb.active  # สมมติว่า sheet แรกคือที่เราต้องการอ่าน

        ws = wb['register']
        for row in ws:
            values = [cell.value for cell in row]
            if values[0] != 'id':
                user = User.objects.create_user(
                    username=values[1],  # username
                    email=values[2],  # email
                    password=str(values[8]),  # ใช้ password จาก values[8]
                    pk=values[0],  # ใช้ id ของผู้ใช้
                    first_name=values[3],  # first_name
                    last_name=values[4]  # last_name
                )
                register, created = Profile.objects.get_or_create(user=user, location=values[7],gender=values[5],age=values[6],role=values[10])

        ws_questionnaire = wb['questionnaire']
        for row in ws_questionnaire.iter_rows(min_row=2, values_only=True):  # Skipping header row
            questionnaire_id, name, description = row


            questionnaire, created = Questionnaire.objects.get_or_create(
                id=questionnaire_id,  # This is the field we are looking to match
                defaults={'questionnaire_name': name, 'description': description}
                # This will set the fields if the record doesn't exist
            )

        ws_questions = wb['question']
        for row in ws_questions.iter_rows(min_row=2, values_only=True):  # Skipping header row
            question_id, questionnaire_id, content = row

            # Get or create the questionnaire
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)

            # Get or create the question
            question, created = Question.objects.get_or_create(
                id=question_id,
                defaults={'questionnaire': questionnaire, 'question_content': content}
            )

        # 4. Load "Choice" sheet
        ws_choice = wb['choice']
        for row in ws_choice.iter_rows(min_row=2, values_only=True):  # Skipping header row
            response_id, question_id, response_value, response_text = row
            question = Question.objects.get(id=question_id)

            # Get or create the choice
            choice, created = Choice.objects.get_or_create(
                id=response_id,
                defaults={'question': question, 'response_value': response_value, 'response_text': response_text}
            )

        # 5. Load "Results" sheet
        ws_results = wb['result']
        for row in ws_results.iter_rows(min_row=2, values_only=True):  # Skipping header row
            result_id, questionnaire_id, score_low, score_high, stress_level, result_description = row
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)

            # Get or create the result
            result, created = Result.objects.get_or_create(
                id=result_id,
                defaults={'questionnaire': questionnaire, 'score_low': score_low, 'score_high': score_high,
                          'stress_level': stress_level, 'result_description': result_description}
            )

        self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))

