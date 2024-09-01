from DiscTracker.database import initialise_database, add_item
from DiscTracker.api import fetch_item
from DiscTracker.price_checker_service import check_price_updates

if __name__ == "__main__":
    initialise_database()
    
    while True:
        print("\n1. Add An Item By CEX ID")
        print("2. View Current Prices")
        print("5. Generate Price Change Report")
        print("6. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            id = input("Enter the ID of the Blu-ray/DVD: ")
            item = fetch_item(id)
            if item:
                add_item(item)
        elif choice == '2':
            check_price_updates()
        elif choice == '3':
            generate_report()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")