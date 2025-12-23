import tkinter as tk
from controller import FinanceController


def main():
    root = tk.Tk()
    app = FinanceController(root)

    def on_closing():
        app.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()