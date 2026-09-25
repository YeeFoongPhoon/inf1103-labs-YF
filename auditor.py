import threading
import time

inventory = 0
total = 0
error_count = 0
while True:
  user_input = input("Please enter an integer of the stock count: ")
  if user_input.lower() == "q":
    print(f"\nExiting... Final total sum: {total}", f"Total error count: {error_count}")
    break

  try:
    inventory = int(user_input)
    print(f"Success! You entered the integer of the stock count {inventory}")
    if inventory < 0:
      raise ValueError
    if inventory > 500:
        print("Inventory count is too high. Please enter a value less than or equal to 500.\n")
        break
    total += inventory
    print(f"-> Added {inventory}. Current total: {total}\n")
  except ValueError:
  
    print("Inventory Invalid or you have entered a non integer value. Please enter a valid integer of the stock count or 'q' to quit.\n")
    error_count += 1
    continue