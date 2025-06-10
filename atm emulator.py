import os
import json
from decimal import Decimal


class ATMError(Exception):
    """Base exception for ATM operations."""
    pass


class ATM:
    """Simplified ATM simulator with core functionality in Indian Rupees."""
    
    def __init__(self, balance=5000.0, pin="1234", data_file="atm_data.json"):
        self.balance = Decimal(str(balance))
        self.pin = pin
        self.data_file = data_file
        self.transactions = []
        self.authenticated = False
        self.pin_attempts = 0
        self.max_attempts = 3
        self.daily_limit = Decimal('50000.00')  # ₹50,000 daily limit
        self.daily_withdrawn = Decimal('0.00')
        self.load_data()

    def load_data(self):
        """Load ATM data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.balance = Decimal(data.get('balance', '5000.00'))
                    self.pin = data.get('pin', '1234')
                    self.transactions = data.get('transactions', [])
                    self.daily_withdrawn = Decimal(data.get('daily_withdrawn', '0.00'))
        except Exception:
            pass  # Use defaults if file doesn't exist or is corrupted

    def save_data(self):
        """Save ATM data to file."""
        try:
            data = {
                'balance': str(self.balance),
                'pin': self.pin,
                'transactions': self.transactions,
                'daily_withdrawn': str(self.daily_withdrawn)
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass  # Fail silently if can't save

    def authenticate(self):
        """Authenticate user with PIN."""
        if self.authenticated:
            return True
            
        if self.pin_attempts >= self.max_attempts:
            raise ATMError("Card locked due to too many failed attempts.")
        
        entered_pin = input("Enter PIN: ").strip()
        
        if entered_pin == self.pin:
            self.authenticated = True
            self.pin_attempts = 0
            return True
        else:
            self.pin_attempts += 1
            remaining = self.max_attempts - self.pin_attempts
            if remaining > 0:
                print(f"Incorrect PIN. {remaining} attempts remaining.")
                return False
            else:
                raise ATMError("Card locked due to too many failed attempts.")

    def validate_amount(self, amount):
        """Validate transaction amount."""
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ATMError("Amount must be positive.")
            return amount_decimal.quantize(Decimal('0.01'))
        except (ValueError, TypeError):
            raise ATMError("Invalid amount format.")

    def record_transaction(self, trans_type, amount):
        """Record transaction in history."""
        import datetime
        transaction = {
            'type': trans_type,
            'amount': str(amount),
            'balance': str(self.balance),
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.transactions.append(transaction)
        if len(self.transactions) > 50:  # Keep only last 50 transactions
            self.transactions = self.transactions[-50:]

    def check_balance(self):
        """Display current balance."""
        print(f"\nCurrent Balance: ₹{self.balance:.2f}")
        print(f"Daily Withdrawal Remaining: ₹{self.daily_limit - self.daily_withdrawn:.2f}")

    def deposit(self):
        """Deposit money into account."""
        try:
            amount_input = input("Enter deposit amount: ₹")
            amount = self.validate_amount(amount_input)
            
            if amount > Decimal('100000.00'):  # ₹1 lakh maximum deposit
                raise ATMError("Maximum deposit amount is ₹1,00,000.00")
            
            old_balance = self.balance
            self.balance += amount
            self.record_transaction("Deposit", amount)
            
            print(f"✓ Deposited ₹{amount:.2f}")
            print(f"Previous balance: ₹{old_balance:.2f}")
            print(f"New balance: ₹{self.balance:.2f}")
            
        except ATMError as e:
            print(f"Error: {e}")
        except Exception:
            print("Error: Invalid input.")

    def withdraw(self):
        """Withdraw money from account."""
        try:
            amount_input = input("Enter withdrawal amount: ₹")
            amount = self.validate_amount(amount_input)
            
            # Check for standard ATM denominations (₹100, ₹200, ₹500, ₹2000)
            if amount % 100 != 0:
                raise ATMError("Amount must be in multiples of ₹100")
            
            if self.daily_withdrawn + amount > self.daily_limit:
                remaining = self.daily_limit - self.daily_withdrawn
                raise ATMError(f"Daily limit exceeded. Remaining: ₹{remaining:.2f}")
            
            if amount > self.balance:
                raise ATMError(f"Insufficient funds. Available: ₹{self.balance:.2f}")
            
            old_balance = self.balance
            self.balance -= amount
            self.daily_withdrawn += amount
            self.record_transaction("Withdrawal", -amount)
            
            print(f"✓ Withdrew ₹{amount:.2f}")
            print(f"Previous balance: ₹{old_balance:.2f}")
            print(f"New balance: ₹{self.balance:.2f}")
            
        except ATMError as e:
            print(f"Error: {e}")
        except Exception:
            print("Error: Invalid input.")

    def transfer(self):
        """Transfer funds to another account."""
        try:
            account = input("Enter recipient account (10 digits): ").strip()
            if len(account) != 10 or not account.isdigit():
                raise ATMError("Invalid account number. Must be 10 digits.")
            
            amount_input = input("Enter transfer amount: ₹")
            amount = self.validate_amount(amount_input)
            fee = Decimal('5.00')  # ₹5 transfer fee
            total = amount + fee
            
            if total > self.balance:
                raise ATMError(f"Insufficient funds (including ₹{fee:.2f} fee).")
            
            print(f"\nTransfer to: ****{account[-4:]}")
            print(f"Amount: ₹{amount:.2f}")
            print(f"Fee: ₹{fee:.2f}")
            print(f"Total: ₹{total:.2f}")
            
            confirm = input("Confirm (y/n): ").strip().lower()
            if confirm != 'y':
                print("Transfer cancelled.")
                return
            
            old_balance = self.balance
            self.balance -= total
            self.record_transaction("Transfer", -amount)
            
            print(f"✓ Transfer completed")
            print(f"Previous balance: ₹{old_balance:.2f}")
            print(f"New balance: ₹{self.balance:.2f}")
            
        except ATMError as e:
            print(f"Error: {e}")
        except Exception:
            print("Error: Invalid input.")

    def view_history(self):
        """Display transaction history."""
        if not self.transactions:
            print("No transactions found.")
            return
        
        print("\n=== TRANSACTION HISTORY ===")
        print("Date & Time          Type        Amount        Balance")
        print("-" * 58)
        
        for trans in self.transactions[-10:]:  # Show last 10
            amount = Decimal(trans['amount'])
            balance = Decimal(trans['balance'])
            amount_str = f"₹{amount:.2f}" if amount >= 0 else f"-₹{abs(amount):.2f}"
            
            print(f"{trans['timestamp']:<18} {trans['type']:<10} {amount_str:>12} ₹{balance:.2f}")

    def change_pin(self):
        """Change user PIN."""
        current = input("Enter current PIN: ").strip()
        if current != self.pin:
            print("Incorrect current PIN.")
            return
        
        new_pin = input("Enter new 4-digit PIN: ").strip()
        if len(new_pin) != 4 or not new_pin.isdigit():
            print("PIN must be 4 digits.")
            return
        
        confirm = input("Confirm new PIN: ").strip()
        if new_pin != confirm:
            print("PINs do not match.")
            return
        
        self.pin = new_pin
        print("✓ PIN changed successfully!")

    def run(self):
        """Main ATM program loop."""
        print("=== Welcome to ATM System ===")
        
        try:
            while True:
                if not self.authenticated:
                    try:
                        if not self.authenticate():
                            continue
                    except ATMError as e:
                        print(f"Error: {e}")
                        break
                
                print("\n=== ATM MENU ===")
                print("1. Check Balance")
                print("2. Deposit")
                print("3. Withdraw")
                print("4. Transfer")
                print("5. Transaction History")
                print("6. Change PIN")
                print("7. Exit")
                
                choice = input("\nSelect option (1-7): ").strip()
                
                if choice == '1':
                    self.check_balance()
                elif choice == '2':
                    self.deposit()
                elif choice == '3':
                    self.withdraw()
                elif choice == '4':
                    self.transfer()
                elif choice == '5':
                    self.view_history()
                elif choice == '6':
                    self.change_pin()
                elif choice == '7':
                    print("Thank you for using ATM System!")
                    break
                else:
                    print("Invalid choice. Please select 1-7.")
                
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\nSession terminated.")
        finally:
            self.save_data()


if __name__ == "__main__":
    atm = ATM()
    atm.run()
