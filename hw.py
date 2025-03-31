# Task 1, domain of Email
email = input("Enter your email: ") # Prompts user to input email
atsymbol = email.find("@") # locates the @ symbol
dot = email.find(".", atsymbol) # locates the .
print(email[atsymbol + 1: dot]) # prints between @ and .




# Task 2: Name Abbreviation
full = input("Enter full name: ")  # Prompts user to input full name
names = full.split()  # Splits name into parts
print(".".join(name[0].upper() for name in names) + ".")  # Creates initials with dots




# Task 3: Validate Date Format
date = input("Enter date (DD/MM/YYYY): ")  # Prompts user to input date
parts = date.split('/')  # Splits date into day month and year
if len(parts) == 3 and len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
    print("Valid date format")  # Checks length of each part and if correct prints "Valid"
else:
    print("Invalid date format")  # Prints "Invalid" if format doesn't match


# Used AI to help complete the last 2 as I was very lost


# Task 4: Extract Substring Between Symbols
text = input("Enter text with brackets: ")  # Prompts user to input text
start = text.find('[') + 1  # Finds starting index after '['
end = text.find(']', start)  # Finds ending index at ']'
if start > 0 and end > start:  # Checks if both brackets are found
    print(text[start:end])  # Prints substring between brackets
else:
    print("No brackets found")  # Prints message if brackets are missing



# Task 5: String Repetition Checker
s = input("Enter string to check repetition: ")  # Prompts user to input string
for i in range(1, len(s) + 1):  # Loops through substring lengths
    if s[:i] * (len(s) // i) == s:  # Checks if substring repeats to form the string
        print(s[:i])  # Prints the shortest repeating substring
        break