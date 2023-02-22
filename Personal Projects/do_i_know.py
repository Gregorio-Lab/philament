# Making CLI Address Book
from pickle import dump, load
from os import system
from time import sleep
from sys import exit

heading = """
                 Address Book
-----------------------------------------------
"""
help_text = "For List of Commands, type 'help'"


def loading():
    sleep(1)
    print("Going back to main menu...")
    sleep(2)


def show_info(info_list):
    for name in info_list:
        print(f"-{name}")


def display_contacts(address_book):
    system("cls")
    for contact in range(0, len(address_book)):
        print(
            f"{contact+1} | Name: {address_book[contact][0]} {address_book[contact][1]}"
        )
    input(">>")


def repeat_name(address_book, name_locations):
    names = []
    for i in name_locations:
        names.append(address_book[i])
    print(names)


def backwards_adding():
    # Here the order im thinking but im feeling too lazy rn

    # take list as input, and use the length to determine what step its in, if len = 1
    # Youre at the second step, ie last name

    # use.pop() to just get rid of the last one, and then just return
    # and make sure the variable assigned to this function replaces
    # the existing list

    # Thats it, and then just do it over again for each step, but where you take input again
    # IDK how to handle going back mutiple times
    pass


def admin_powers(address_book):
    display_contacts(address_book)
    x = input("Enter index to delete:")

    pass


# Apologies for the shit ton of repeating code, I don't know how to do this better :'(
def add_contact(address_book: list) -> list:

    print("To skip any of the field entries, just enter 'skip'")
    input_info = []

    print("Enter first name:")
    fName = input(">").strip().lower()

    try:
        while fName == "skip" or fName == "":
            print("Sorry first name cannot be skipped or blank")
            sleep(1)
            system("cls")
            print("Enter first name:")
            fName = input().strip().lower()

    except NameError:
        pass

    input_info.append(fName.capitalize())
    system("cls")

    show_info(input_info)
    print("Enter last name:")
    lName = input().strip().lower()
    if lName == "skip":
        lName = None
        input_info.append(lName)

    else:
        input_info.append(lName.capitalize())

    system("cls")

    show_info(input_info)
    print("Enter address:")
    address = input().strip().lower()
    if address == "skip":
        address = None

    input_info.append(address)
    system("cls")

    show_info(input_info)
    print("Enter phone number (no dashes or spaces):")
    phone = input().strip().lower()
    if phone == "skip":
        phone = None

    input_info.append(phone)
    system("cls")

    show_info(input_info)
    print("Enter email address:")
    email = input().strip().lower()
    if email == "skip":
        email = None

    input_info.append(email)
    system("cls")

    adding_contact = [fName, lName, address, phone, email]
    address_book.append(adding_contact)

    with open("contactos.pickle", "wb") as writer:
        dump(address_book, writer)

    print(f"Added {adding_contact[0]} to Address Book!")
    loading()


def delete_contact(address_book: list) -> list:
    edit_index = []

    system("cls")
    print(
        heading + "Type first name of desired contact, otherwise type 'show contacts'"
    )
    search = input(">>").lower()
    search = search.replace(" ", "")

    if search == "showcontacts":
        display_contacts(address_book)
        print("Type first name of desired contact")
        search = input(">>").lower().strip()

    for contact in address_book:
        if contact[0].lower() == search:
            edit_index.append(address_book.index(contact))

        elif search == "exit":
            return

    if len(edit_index) == 0:
        system("cls")

        print(
            f"{heading}Sorry, I couldn't find {search.capitalize()} in the address book!"
        )
        loading()
        return

    elif len(edit_index) > 1:
        print(f"More than one {search.capitalize()} was found!")
        edit_index = [repeat_name(address_book, edit_index)]
        return

    del address_book[edit_index[0]]

    return address_book


def reset_book(address_book):

    print(heading)
    print("Are you SURE that you want to delete the entire address book? (y\\n)")
    answer = input(">>").lower().strip()

    if answer != "y":
        return
    system("cls")

    print(heading)
    print("Type 'deleteAddressBook' to confirm (capitalization doesn't matter):")
    answer = input(">>").lower().strip()

    if answer != "deleteaddressbook":
        loading()
        return

    system("cls")
    print(heading)

    address_book = []
    with open("contactos.pickle", "wb") as writer:
        dump(address_book, writer)

    print("Address book has been cleared!")
    loading()


def search_contacts():
    pass


try:
    with open("contactos.pickle", "rb") as reader:
        book = load(reader)

except FileNotFoundError:
    book = []


# Running loop:
########################################################
while True:
    system("cls")
    print(heading + help_text)

    command = input(">>").strip().lower()

    # remember to make all the command elif start with system('cls')
    # just for consistencys sake!

    if command == "add":
        add_contact(book)

    elif command == "help":
        system("cls")
        print(
            heading
            + """
Command List:
add -> add new contact
edit -> edit contact
delete -> delete contact (WIP)
search -> search for contacts (WIP)
show -> display all contacts
reset -> clear entire address book
exit -> exit program
"""
        )

        input("Hit enter to return to the main menu\n")

    elif command == "edit":
        system("cls")
        book = delete_contact(book)
        add_contact(book)

    elif command == "show":
        system("cls")
        display_contacts(book)

    elif command == "exit":
        system("cls")
        print("Goodbye!")
        sleep(1)
        exit()
    elif command == "delete":
        system("cls")
        book = delete_contact(book)

    elif command == "reset":
        system("cls")
        reset_book(book)

    elif command == "hello" or command == "hi":
        system("cls")
        print(f"{heading}Hello there! I hope you're having a good day ʕ•ᴥ•ʔﾉ♡")
        sleep(3)

    elif command == "admin":
        system("cls")
        book = admin_powers(book)

    else:
        print("Please enter a command!")
        sleep(1)
