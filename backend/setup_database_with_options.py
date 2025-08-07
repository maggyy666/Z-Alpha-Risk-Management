#!/usr/bin/env python3
"""
Database setup with options: generate new data or import existing sample data
"""

import os
import sys
import subprocess
from datetime import datetime

def show_menu():
    """Show setup options menu"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DATABASE SETUP")
    print("=" * 60)
    print("\nChoose setup option:")
    print("1. Generate new sample data (requires time for data generation)")
    print("2. Import pre-generated sample data (quick setup)")
    print("3. Exit")
    print("=" * 60)

def get_user_choice():
    """Get user's choice"""
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\nSetup cancelled by user.")
            sys.exit(0)
        except Exception:
            print("Invalid input. Please enter 1, 2, or 3.")

def check_sample_data_file():
    """Check if sample data file exists"""
    sample_file = "z_alpha_sample_database.json"
    if os.path.exists(sample_file):
        file_size = os.path.getsize(sample_file)
        file_size_mb = file_size / (1024 * 1024)
        print(f"✅ Sample data file found: {sample_file} ({file_size_mb:.2f} MB)")
        return True
    else:
        print(f"❌ Sample data file not found: {sample_file}")
        return False

def run_script(script_name, description):
    """Run a Python script"""
    print(f"\n{description}...")
    print(f"Running: python {script_name}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              check=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def setup_with_new_data():
    """Setup database with newly generated data"""
    print("\n" + "=" * 60)
    print("SETTING UP WITH NEW DATA GENERATION")
    print("=" * 60)
    print("This will generate fresh sample data. This process may take several minutes...")
    
    if not run_script("setup_database.py", "Database setup with new data generation"):
        return False
    
    # After successful setup, create export for future use
    print("\nCreating export for future installations...")
    if run_script("export_database.py", "Database export"):
        print("✅ Sample data export created for future quick installations!")
    
    return True

def setup_with_sample_data():
    """Setup database with pre-generated sample data"""
    print("\n" + "=" * 60)
    print("SETTING UP WITH SAMPLE DATA")
    print("=" * 60)
    
    # Check if sample data file exists
    if not check_sample_data_file():
        print("\nSample data file not found!")
        print("Options:")
        print("1. Download sample data from project repository")
        print("2. Generate new data instead")
        print("3. Exit and manually place the sample data file")
        
        choice = input("\nWhat would you like to do? (1-3): ").strip()
        
        if choice == "1":
            print("Please download 'z_alpha_sample_database.json' from the project repository")
            print("and place it in the backend/ directory, then run this script again.")
            return False
        elif choice == "2":
            return setup_with_new_data()
        else:
            return False
    
    if not run_script("import_database.py", "Database import from sample data"):
        return False
    
    return True

def delete_existing_database():
    """Delete existing database if it exists"""
    db_path = "portfolio.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"✅ Existing database {db_path} deleted")
        except Exception as e:
            print(f"❌ Error deleting existing database: {e}")
            return False
    else:
        print("No existing database found")
    return True

def main():
    """Main setup function"""
    print("Welcome to Z-Alpha Securities Database Setup!")
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 3:
            print("Setup cancelled. Goodbye!")
            sys.exit(0)
        
        # Delete existing database
        print("\nCleaning up existing database...")
        if not delete_existing_database():
            print("Failed to clean up existing database!")
            continue
        
        success = False
        
        if choice == 1:
            success = setup_with_new_data()
        elif choice == 2:
            success = setup_with_sample_data()
        
        if success:
            print("\n" + "=" * 60)
            print("SETUP COMPLETE!")
            print("=" * 60)
            print("Database is ready for use!")
            print("You can now run the application with: python start_all.py")
            break
        else:
            print("\n" + "=" * 60)
            print("SETUP FAILED!")
            print("=" * 60)
            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)