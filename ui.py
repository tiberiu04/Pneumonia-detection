import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
from PIL import Image, ImageTk
from predict import predict


class PneumoniaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🩺 Pneumonia Detector")
        self.root.geometry("600x800")

        # 💻 HEADER „ca pe site”
        header_frame = ttk.Frame(root, bootstyle=PRIMARY, padding=20)
        header_frame.pack(fill=X)

        header_label = ttk.Label(
            header_frame,
            text="🩺 Pneumonia Detector",
            font=("Helvetica", 26, "bold"),
            bootstyle=INVERSE
        )
        header_label.pack()

        # 📝 SUBHEADER
        subheader = ttk.Label(
            root,
            text="Radiologist-level Pneumonia Detection\nfrom Chest X-rays using Deep Learning",
            font=("Helvetica", 14, "italic"),
            bootstyle=INFO,
            justify=CENTER
        )
        subheader.pack(pady=20)

        # 📷 IMAGE FRAME
        self.image_frame = ttk.Frame(root, padding=10, bootstyle=LIGHT)
        self.image_frame.pack(pady=20)

        self.panel = ttk.Label(self.image_frame)
        self.panel.pack()

        # 📁 SELECT BUTTON
        self.button = ttk.Button(
            root,
            text="📷 Select Image",
            command=self.select_image,
            bootstyle=SUCCESS,
            width=25
        )
        self.button.pack(pady=20)

        # 📊 RESULT LABEL
        self.result_label = ttk.Label(
            root,
            text="",
            font=("Helvetica", 18, "bold"),
            wraplength=500,
            justify=CENTER
        )
        self.result_label.pack(pady=30)

        # 📄 FOOTER
        footer = ttk.Label(
            root,
            text="Created with ❤️ using Deep Learning & Tkinter",
            font=("Helvetica", 10),
            bootstyle=SECONDARY,
            justify=CENTER
        )
        footer.pack(side=BOTTOM, pady=10)

    def select_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if path:
            # display image
            img = Image.open(path)
            img.thumbnail((500, 500))
            img_tk = ImageTk.PhotoImage(img)
            self.panel.config(image=img_tk)
            self.panel.image = img_tk

            # predict & capture output
            from io import StringIO
            import sys

            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            try:
                predict(path)
            except Exception as e:
                mystdout.write(f"Error: {e}")
            sys.stdout = old_stdout

            result = mystdout.getvalue().strip()

            # colorize result
            if "PNEUMONIA" in result:
                color = "danger"
            elif "NORMAL" in result:
                color = "success"
            else:
                color = "warning"

            self.result_label.config(text=result, bootstyle=color)


if __name__ == "__main__":
    app = ttk.Window(themename="cosmo")  # sau flatly, minty, etc.
    PneumoniaApp(app)
    app.mainloop()
