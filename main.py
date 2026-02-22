from database import create_tables
from queue_logic import join_queue, call_next, mark_done, view_queue, view_history, count_waiting, delete_record, clear_all_records


def show_menu():
    """Prints the main menu options."""
    print("\n=============================")
    print("   🏥  QUEUE SYSTEM MENU")
    print("=============================")
    print("  [1]  Join Queue")
    print("  [2]  Call Next Customer")
    print("  [3]  Mark Customer as Done")
    print("  [4]  View Waiting Queue")
    print("  [5]  View Full History")
    print("  [6]  Delete a Record")
    print("  [7]  Clear All Records")
    print("  [0]  Exit")
    print("=============================")


def main():
    """Main loop — initialises the database then keeps showing the menu."""
    create_tables()

    while True:
        show_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            name = input("Enter customer name: ").strip()
            if name:
                join_queue(name)
            else:
                print("\n⚠️  Name cannot be empty.")

        elif choice == "2":
            call_next()

        elif choice == "3":
            mark_done()

        elif choice == "4":
            view_queue()

        elif choice == "5":
            view_history()

        elif choice == "6":
            delete_record()

        elif choice == "7":
            clear_all_records()

        elif choice == "0":
            print("\n👋 Goodbye! Queue system closed.")
            break

        else:
            print("\n❌ Invalid choice. Please pick a number from the menu.")


if __name__ == "__main__":
    main()
