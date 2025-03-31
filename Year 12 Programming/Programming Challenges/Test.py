# Input integer
num = input("Please enter a 3 digit number ")

# Convert the integer to a string, then split and convert each character back to an integer
list = [int(digit) for digit in str(num)]

# Output the result
print(list[0], "Hundreds")
print(list[1], "Tens")
print(list[2], "Ones")
