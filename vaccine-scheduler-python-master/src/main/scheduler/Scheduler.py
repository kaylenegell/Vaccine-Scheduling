from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    #create_patient <username> <password>
    print('check 0')
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    print('check 1')
    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    print('check 2')
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    print('check 3')
    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    print('check 4')
    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False

def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patient WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient

    pass


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    cm = ConnectionManager()
    conn = cm.create_connection()

    #user needs to be logged in
    global current_caregiver
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return
    
    date = tokens[1].split('-')

    month = date[0]
    day = date[1]
    year = date[2]

    time = datetime.datetime(int(year), int(month), int(day))

    select_username = 'SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username'
    select_doses = 'SELECT Name, Doses FROM Vaccines'
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, time)
        for row in cursor:
            print(row['Username'])
        cursor.execute(select_doses)
        for row in cursor:
            print(row['Name'], row['Doses'])
    except pymssql.Error:
        print('Please try again!')
        quit()
    except Exception:
        print('Please try again!')
        quit()
    finally:
        cm.close_connection()
    return False


def reserve(tokens):

    cm = ConnectionManager()
    conn = cm.create_connection()

    #if no one logged in
    global current_patient
    global current_caregiver
    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return
    
    #if not a patient
    if current_patient is None:
        print("Please login as a patient!")
        return


    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return
    
    date = tokens[1]
    vaccine = tokens[2]

    select_username = 'SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username'
    select_vaccine = 'SELECT Name FROM Vaccines WHERE Doses > 0 AND Name = %s'
    select_highest_appointment_id = 'SELECT MAX(AppointmentID) AS id FROM Appointments'

    try:
        #check if there are available caregivers
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, date)
        caregiver = cursor.fetchone()['Username']
        if caregiver is None:
            print("No Caregiver is available!")
            return
        
        #check if there are enough doses
        cursor.execute(select_vaccine, vaccine)
        vaccine = cursor.fetchone()['Name']
        if vaccine is None:
            print("Not enough available doses!")
            return
        
        #if there are enough doses and caregivers, then reserve
        #get appointment id
        cursor.execute(select_highest_appointment_id)
        appointment_id = cursor.fetchone()['id'] + 1

        #update the doses
        update_doses = 'UPDATE Vaccines SET Doses = Doses - 1 WHERE Name = %s'
        cursor.execute(update_doses, vaccine)
        #update caregiver availability (drop caregiver from that availability day)
        update_availability = 'DELETE FROM Availabilities WHERE Username = %s AND Time = %s'
        cursor.execute(update_availability, caregiver, date)

        #insert into appointments - need appointment id, auto increment the appointment id
        insert_appointment = 'INSERT INTO Appointments (AppointmentID, Username, Caregiver, Time, Vaccine) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(insert_appointment, appointment_id, current_patient, caregiver, date, vaccine)
        #output to user
        print('Appointment ID', appointment_id, 'Caregiver username', caregiver)
    except pymssql.Error:
        print('Please try again!')
        quit()
    except Exception:
        print('Please try again!')
        quit()
    finally:
        cm.close_connection()
    return False


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    cm = ConnectionManager()
    conn = cm.create_connection()

    global current_patient
    global current_caregiver

    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return
    
    if current_patient is not None:

        select_appointments = 'SELECT AppointmentId, Vaccine, Time, Caregiver FROM Appointments WHERE Patient = %s'
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(select_appointments, current_patient)
            for row in cursor:
                print(row['AppointmentId'], row['Vaccine'], row['Time'], row['Caregiver'])
        except pymssql.Error as e:
            print('Please try again!')
            quit()
        except Exception as e:
            print('Please try again!')
            quit()
        finally:
            cm.close_connection()
        return False
    
    if current_caregiver is not None:
        
        select_appointments = 'SELECT AppointmentId, Vaccine, Time, Patient FROM Appointments WHERE Caregiver = %s'
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(select_appointments, current_caregiver)
            for row in cursor:
                print(row['AppointmentId'], row['Vaccine'], row['Time'], row['Patient'])
        except pymssql.Error as e:
            print('Please try again!')
            quit()
        except Exception as e:
            print('Please try again!')
            quit()
        finally:
            cm.close_connection()
        return False


def logout(tokens):

    global current_patient
    global current_caregiver

    if current_patient is not None or current_caregiver is not None:
        print("Sucessfully logged out!")
        current_patient = None
        current_caregiver = None

    elif current_patient is None and current_caregiver is None:
        print('Please login first!')

    else:
        print("Please try again!")



def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
