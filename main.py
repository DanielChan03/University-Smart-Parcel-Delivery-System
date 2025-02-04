from webapp import create_app
from webapp.create_admin import create_admin
from webapp.create_manager import create_parcel_manager
from webapp.create_studentStaff import create_student_staff
from webapp.create_courier import create_courier
from webapp.create_uni import create_university
import random

app = create_app()

import random

if __name__ == '__main__':
    app.run()
    