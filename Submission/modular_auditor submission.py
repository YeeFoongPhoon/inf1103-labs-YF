


def get_valid_input(user_input, total, error_count,tax_amount,current_total): 
  if user_input.lower() == "q": 
      return generate_report(total, error_count, tax_amount, current_total)
  try:
    inventory = int(user_input)
    print(f"Success! You entered the integer of the stock count {inventory}")
    if inventory < 0:
      raise ValueError
    if inventory > 500:
        print("Inventory count is too high. Please enter a value less than or equal to 500.\n")
        return total, error_count, False
    total += inventory
    print(f"-> Added {inventory}. Current total stock count: {total}\n")
    return total, error_count, True, inventory
  except ValueError:
    print("Inventory Invalid or you have entered a non integer value. Please enter a valid integer of the stock count or 'q' to quit.\n")
    error_count += 1
    return total, error_count, True, 0


def process_delivery(current_total, inventory):
  delivery_cost = inventory * 10
  current_total += delivery_cost
  print(f"-> Delivery Cost Added: ${delivery_cost} (based on {inventory} stock units). Cumulative Delivery Cost: ${current_total}\n")
  return current_total

def calculate_tax(amount):
  current_total = amount
  tax_rate = 0.10
  tax_amount = current_total * tax_rate
  print(f"Tax amount for the total deliveries processed: {tax_amount:.2f}\n")
  return tax_amount


def generate_report(total, error_count, tax_amount,current_total):
   print("\n=== Final Report ===")
   print(f"\nExiting... Total Deliveries Processed {total}", f"Number of Failed/Rejected Entries: {error_count}")
   print(f"Total Tax Amount: {tax_amount:.2f}")
   print(f"Final Total Amount: {current_total + tax_amount:.2f}\n")
   return True


def main():
    total = 0
    error_count = 0
    current_total = 0
    tax_amount = 0.0
    
    print("=== Inventory & Delivery Management System ===")
    print("Type 'q' at any prompt to quit and view the final report.\n")
    
    while True:
        user_input = input("Enter inventory count: ")
        
        
        result = get_valid_input(user_input, total, error_count, tax_amount, current_total)
        
     
        if result is True:
            break
            
        total, error_count, success, inventory = result
        
        if success and user_input.lower() != "q" and inventory > 0: 
          current_total = process_delivery(current_total, inventory) 
          tax_amount = calculate_tax(current_total)
      
      

if __name__ == "__main__":
    main()