import tkinter as tk
from tkinter import filedialog, messagebox


def new_note():
    text.delete("1.0", tk.END)


def open_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Text Files", "*.txt")]
    )

    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            text.delete("1.0", tk.END)
            text.insert(tk.END, file.read())
    except Exception as e:
        messagebox.showerror("Error", str(e))


def save_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")]
    )

    if not file_path:
        return

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text.get("1.0", tk.END))

        messagebox.showinfo("Saved", "Note saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))


root = tk.Tk()
root.title("Desktop Notes")
root.geometry("700x500")

menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)

file_menu.add_command(label="New", command=new_note)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

text = tk.Text(
    root,
    wrap="word",
    font=("Arial", 12)
)

text.pack(expand=True, fill="both")

root.mainloop()