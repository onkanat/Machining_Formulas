#!/usr/bin/env python3
# -*- coding : utf-8 -*-
# V3 GUI - Simple Working Version
# Autor: Hakan KILIÇASLAN 2025
# flake8: noqa

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import math


class SimpleV3Calculator:
    """Simple working V3 Calculator with focus on functionality."""

    def __init__(self, root: tk.Tk):
        self.root = root

        # Force window to appear immediately
        root.withdraw()  # Hide initially
        self.setup_ui()
        root.deiconify()  # Show after setup
        root.lift()  # Bring to front
        root.focus_force()  # Force focus

    def setup_ui(self):
        """Setup the main interface."""
        # Configure root window
        self.root.title("🔧 Mühendislik Hesaplayıcı V3 - Working")
        self.root.geometry("1200x800")

        # Force window to be visible
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(lambda: self.root.attributes("-topmost", False))

        # Configure styles
        style = ttk.Style()
        style.theme_use("clam")

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Force update
        self.root.update_idletasks()

        # Create paned window
        self.paned = ttk.PanedWindow(main_frame, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        # Left panel - Calculations
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        # Right panel - Workspace
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        # Create calculation panels
        self.create_calculation_panel(left_frame)

        # Create workspace panel
        self.create_workspace_panel(right_frame)

        # Set initial focus
        self.root.after(100, lambda: self.diameter_entry.focus_set())

    def create_calculation_panel(self, parent):
        """Create calculation tools panel."""
        # Model configuration
        model_frame = ttk.LabelFrame(parent, text="🤖 Model Yapılandırması")
        model_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(model_frame, text="URL:").pack(anchor="w", padx=5)
        self.url_entry = ttk.Entry(model_frame, width=30)
        self.url_entry.pack(padx=5, pady=2)
        self.url_entry.insert(0, "http://localhost:11434")

        ttk.Label(model_frame, text="Model:").pack(anchor="w", padx=5)
        self.model_combo = ttk.Combobox(
            model_frame, values=["bc-coder:latest", "qwen2.5:1.5b-instruct"], width=27
        )
        self.model_combo.pack(padx=5, pady=2)
        self.model_combo.set("bc-coder:latest")

        # Create notebook for calculations
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Create tabs
        self.create_turning_tab()
        self.create_milling_tab()
        self.create_material_tab()

    def create_turning_tab(self):
        """Create turning calculations tab."""
        turning_frame = ttk.Frame(self.notebook)
        self.notebook.add(turning_frame, text="Tornalama")

        ttk.Label(
            turning_frame, text="Tornalama Hesaplamaları", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Cutting speed calculation
        cs_frame = ttk.LabelFrame(turning_frame, text="Kesme Hızı")
        cs_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(cs_frame, text="Çap (mm):").pack(anchor="w", padx=5)
        self.diameter_entry = ttk.Entry(cs_frame, width=20)
        self.diameter_entry.pack(padx=5, pady=2)
        self.diameter_entry.insert(0, "100")

        ttk.Label(cs_frame, text="Devir (rpm):").pack(anchor="w", padx=5)
        self.rpm_entry = ttk.Entry(cs_frame, width=20)
        self.rpm_entry.pack(padx=5, pady=2)
        self.rpm_entry.insert(0, "1000")

        ttk.Button(cs_frame, text="Hesapla", command=self.calculate_cutting_speed).pack(
            pady=5
        )
        self.cs_result = ttk.Label(
            cs_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.cs_result.pack(pady=5)

        # Spindle speed calculation
        ss_frame = ttk.LabelFrame(turning_frame, text="İş Mili Devri")
        ss_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(ss_frame, text="Kesme Hızı (m/dak):").pack(anchor="w", padx=5)
        self.vc_entry = ttk.Entry(ss_frame, width=20)
        self.vc_entry.pack(padx=5, pady=2)
        self.vc_entry.insert(0, "314")

        ttk.Label(ss_frame, text="Çap (mm):").pack(anchor="w", padx=5)
        self.ss_diameter_entry = ttk.Entry(ss_frame, width=20)
        self.ss_diameter_entry.pack(padx=5, pady=2)
        self.ss_diameter_entry.insert(0, "100")

        ttk.Button(ss_frame, text="Hesapla", command=self.calculate_spindle_speed).pack(
            pady=5
        )
        self.ss_result = ttk.Label(
            ss_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.ss_result.pack(pady=5)

    def create_milling_tab(self):
        """Create milling calculations tab."""
        milling_frame = ttk.Frame(self.notebook)
        self.notebook.add(milling_frame, text="Frezeleme")

        ttk.Label(
            milling_frame, text="Frezeleme Hesaplamaları", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Table feed calculation
        tf_frame = ttk.LabelFrame(milling_frame, text="Tabla İlerlemesi")
        tf_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(tf_frame, text="Diş Başı İlerleme (mm):").pack(anchor="w", padx=5)
        self.fz_entry = ttk.Entry(tf_frame, width=20)
        self.fz_entry.pack(padx=5, pady=2)
        self.fz_entry.insert(0, "0.1")

        ttk.Label(tf_frame, text="Diş Sayısı:").pack(anchor="w", padx=5)
        self.teeth_entry = ttk.Entry(tf_frame, width=20)
        self.teeth_entry.pack(padx=5, pady=2)
        self.teeth_entry.insert(0, "4")

        ttk.Label(tf_frame, text="Devir (rpm):").pack(anchor="w", padx=5)
        self.milling_rpm_entry = ttk.Entry(tf_frame, width=20)
        self.milling_rpm_entry.pack(padx=5, pady=2)
        self.milling_rpm_entry.insert(0, "2000")

        ttk.Button(tf_frame, text="Hesapla", command=self.calculate_table_feed).pack(
            pady=5
        )
        self.tf_result = ttk.Label(
            tf_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.tf_result.pack(pady=5)

        # Cutting speed calculation
        mc_frame = ttk.LabelFrame(milling_frame, text="Kesme Hızı")
        mc_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(mc_frame, text="Çap (mm):").pack(anchor="w", padx=5)
        self.mc_diameter_entry = ttk.Entry(mc_frame, width=20)
        self.mc_diameter_entry.pack(padx=5, pady=2)
        self.mc_diameter_entry.insert(0, "50")

        ttk.Label(mc_frame, text="Devir (rpm):").pack(anchor="w", padx=5)
        self.mc_rpm_entry = ttk.Entry(mc_frame, width=20)
        self.mc_rpm_entry.pack(padx=5, pady=2)
        self.mc_rpm_entry.insert(0, "2000")

        ttk.Button(
            mc_frame, text="Hesapla", command=self.calculate_milling_cutting_speed
        ).pack(pady=5)
        self.mc_result = ttk.Label(
            mc_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.mc_result.pack(pady=5)

    def create_material_tab(self):
        """Create material calculations tab."""
        material_frame = ttk.Frame(self.notebook)
        self.notebook.add(material_frame, text="Malzeme")

        ttk.Label(
            material_frame, text="Malzeme Hesaplamaları", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Mass calculation
        mass_frame = ttk.LabelFrame(material_frame, text="Kütle Hesabı")
        mass_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(mass_frame, text="Şekil:").pack(anchor="w", padx=5)
        self.shape_combo = ttk.Combobox(
            mass_frame, values=["Daire", "Dikdörtgen", "Kare", "Boru", "Küre"], width=18
        )
        self.shape_combo.pack(padx=5, pady=2)
        self.shape_combo.set("Daire")
        self.shape_combo.bind("<<ComboboxSelected>>", self.update_shape_params)

        # Dynamic parameters frame
        self.params_frame = ttk.Frame(mass_frame)
        self.params_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(mass_frame, text="Yoğunluk (g/cm³):").pack(anchor="w", padx=5)
        self.density_entry = ttk.Entry(mass_frame, width=20)
        self.density_entry.pack(padx=5, pady=2)
        self.density_entry.insert(0, "7.85")

        ttk.Button(mass_frame, text="Hesapla", command=self.calculate_mass).pack(pady=5)
        self.mass_result = ttk.Label(
            mass_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.mass_result.pack(pady=5)

        # Initialize with circle parameters
        self.update_shape_params()

    def update_shape_params(self, event=None):
        """Update shape parameters based on selection."""
        # Clear existing parameter widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        shape = self.shape_combo.get()
        self.param_widgets = {}

        if shape == "Daire":
            ttk.Label(self.params_frame, text="Yarıçap (mm):").pack(anchor="w", padx=5)
            radius_entry = ttk.Entry(self.params_frame, width=20)
            radius_entry.pack(padx=5, pady=2)
            radius_entry.insert(0, "10")
            self.param_widgets["radius"] = radius_entry

            ttk.Label(self.params_frame, text="Uzunluk (mm):").pack(anchor="w", padx=5)
            length_entry = ttk.Entry(self.params_frame, width=20)
            length_entry.pack(padx=5, pady=2)
            length_entry.insert(0, "100")
            self.param_widgets["length"] = length_entry

        elif shape == "Dikdörtgen":
            ttk.Label(self.params_frame, text="Genişlik (mm):").pack(anchor="w", padx=5)
            width_entry = ttk.Entry(self.params_frame, width=20)
            width_entry.pack(padx=5, pady=2)
            width_entry.insert(0, "20")
            self.param_widgets["width"] = width_entry

            ttk.Label(self.params_frame, text="Yükseklik (mm):").pack(
                anchor="w", padx=5
            )
            height_entry = ttk.Entry(self.params_frame, width=20)
            height_entry.pack(padx=5, pady=2)
            height_entry.insert(0, "30")
            self.param_widgets["height"] = height_entry

            ttk.Label(self.params_frame, text="Uzunluk (mm):").pack(anchor="w", padx=5)
            length_entry = ttk.Entry(self.params_frame, width=20)
            length_entry.pack(padx=5, pady=2)
            length_entry.insert(0, "100")
            self.param_widgets["length"] = length_entry

        elif shape == "Kare":
            ttk.Label(self.params_frame, text="Kenar (mm):").pack(anchor="w", padx=5)
            width_entry = ttk.Entry(self.params_frame, width=20)
            width_entry.pack(padx=5, pady=2)
            width_entry.insert(0, "25")
            self.param_widgets["width"] = width_entry

            ttk.Label(self.params_frame, text="Uzunluk (mm):").pack(anchor="w", padx=5)
            length_entry = ttk.Entry(self.params_frame, width=20)
            length_entry.pack(padx=5, pady=2)
            length_entry.insert(0, "100")
            self.param_widgets["length"] = length_entry

        elif shape == "Boru":
            ttk.Label(self.params_frame, text="Dış Yarıçap (mm):").pack(
                anchor="w", padx=5
            )
            outer_radius_entry = ttk.Entry(self.params_frame, width=20)
            outer_radius_entry.pack(padx=5, pady=2)
            outer_radius_entry.insert(0, "15")
            self.param_widgets["outer_radius"] = outer_radius_entry

            ttk.Label(self.params_frame, text="İç Yarıçap (mm):").pack(
                anchor="w", padx=5
            )
            inner_radius_entry = ttk.Entry(self.params_frame, width=20)
            inner_radius_entry.pack(padx=5, pady=2)
            inner_radius_entry.insert(0, "10")
            self.param_widgets["inner_radius"] = inner_radius_entry

            ttk.Label(self.params_frame, text="Uzunluk (mm):").pack(anchor="w", padx=5)
            length_entry = ttk.Entry(self.params_frame, width=20)
            length_entry.pack(padx=5, pady=2)
            length_entry.insert(0, "100")
            self.param_widgets["length"] = length_entry

        elif shape == "Küre":
            ttk.Label(self.params_frame, text="Yarıçap (mm):").pack(anchor="w", padx=5)
            radius_entry = ttk.Entry(self.params_frame, width=20)
            radius_entry.pack(padx=5, pady=2)
            radius_entry.insert(0, "25")
            self.param_widgets["radius"] = radius_entry

    def create_workspace_panel(self, parent):
        """Create workspace editor panel."""
        ttk.Label(parent, text="Çalışma Alanı", font=("Arial", 12, "bold")).pack(pady=5)

        # Create text widget with scrollbar
        import tkinter.scrolledtext as scrolledtext

        self.workspace_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, width=80, height=30
        )
        self.workspace_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Add initial content
        initial_content = """Çalışma Alanı

Bu alana hesaplama sonuçlarınızı ekleyebilirsiniz.

Örnek Hesaplamalar:
• Tornalama Kesme Hızı: 314.16 m/dak
• Frezeleme Tabla İlerlemesi: 800.00 mm/dak
• Malzeme Kütle: 246.62 g

Notlar:
• Tüm hesaplamalar otomatik olarak bu alana eklenebilir
• Model önerileri için metin seçip "Model Düzenleme Öner" kullanın
• Çalışma alanını kaydedebilir ve yükleyebilirsiniz"""

        self.workspace_text.insert("1.0", initial_content)

        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text="Temizle", command=self.clear_workspace).pack(
            side="left", padx=2
        )
        ttk.Button(button_frame, text="Kaydet", command=self.save_workspace).pack(
            side="left", padx=2
        )
        ttk.Button(button_frame, text="Yükle", command=self.load_workspace).pack(
            side="left", padx=2
        )

    # Calculation methods
    def calculate_cutting_speed(self):
        """Calculate cutting speed."""
        try:
            diameter = float(self.diameter_entry.get())
            rpm = float(self.rpm_entry.get())
            vc = (math.pi * diameter * rpm) / 1000
            self.cs_result.config(text=f"Sonuç: {vc:.2f} m/dak")
            self.inject_to_workspace(
                f"Tornalama Kesme Hızı: {vc:.2f} m/dak (Çap: {diameter}mm, Devir: {rpm}rpm)"
            )
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

    def calculate_spindle_speed(self):
        """Calculate spindle speed."""
        try:
            vc = float(self.vc_entry.get())
            diameter = float(self.ss_diameter_entry.get())
            rpm = (vc * 1000) / (math.pi * diameter)
            self.ss_result.config(text=f"Sonuç: {rpm:.0f} rpm")
            self.inject_to_workspace(
                f"Tornalama İş Mili Devri: {rpm:.0f} rpm (Kesme Hızı: {vc}m/dak, Çap: {diameter}mm)"
            )
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

    def calculate_table_feed(self):
        """Calculate table feed."""
        try:
            fz = float(self.fz_entry.get())
            z = float(self.teeth_entry.get())
            rpm = float(self.milling_rpm_entry.get())
            vf = fz * z * rpm
            self.tf_result.config(text=f"Sonuç: {vf:.2f} mm/dak")
            self.inject_to_workspace(
                f"Frezeleme Tabla İlerlemesi: {vf:.2f} mm/dak (fz: {fz}mm, z: {z}, n: {rpm}rpm)"
            )
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

    def calculate_milling_cutting_speed(self):
        """Calculate milling cutting speed."""
        try:
            diameter = float(self.mc_diameter_entry.get())
            rpm = float(self.mc_rpm_entry.get())
            vc = (math.pi * diameter * rpm) / 1000
            self.mc_result.config(text=f"Sonuç: {vc:.2f} m/dak")
            self.inject_to_workspace(
                f"Frezeleme Kesme Hızı: {vc:.2f} m/dak (Çap: {diameter}mm, Devir: {rpm}rpm)"
            )
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

    def calculate_mass(self):
        """Calculate mass."""
        try:
            density = float(self.density_entry.get())
            shape = self.shape_combo.get()

            # Get parameter values
            params = {}
            for param_name, entry in self.param_widgets.items():
                params[param_name] = float(entry.get())

            # Calculate volume based on shape
            if shape == "Daire":
                radius = params["radius"]
                length = params["length"]
                volume = math.pi * radius**2 * length
            elif shape == "Dikdörtgen":
                width = params["width"]
                height = params["height"]
                length = params["length"]
                volume = width * height * length
            elif shape == "Kare":
                width = params["width"]
                length = params["length"]
                volume = width**2 * length
            elif shape == "Boru":
                outer_radius = params["outer_radius"]
                inner_radius = params["inner_radius"]
                length = params["length"]
                volume = math.pi * (outer_radius**2 - inner_radius**2) * length
            elif shape == "Küre":
                radius = params["radius"]
                volume = (4 / 3) * math.pi * radius**3
            else:
                volume = 0

            # Convert to cm³ and calculate mass
            volume_cm3 = volume / 1000
            mass = volume_cm3 * density

            self.mass_result.config(text=f"Sonuç: {mass:.2f} g")
            self.inject_to_workspace(
                f"Malzeme Kütle: {mass:.2f} g ({shape}, Yoğunluk: {density}g/cm³)"
            )

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")

    def inject_to_workspace(self, text):
        """Inject calculation result to workspace."""
        current_content = self.workspace_text.get("1.0", tk.END)
        self.workspace_text.delete("1.0", tk.END)
        self.workspace_text.insert("1.0", current_content.rstrip() + f"\n• {text}\n")

    def clear_workspace(self):
        """Clear workspace."""
        self.workspace_text.delete("1.0", tk.END)
        self.workspace_text.insert("1.0", "Çalışma Alanı\n\nTemizlendi...")

    def save_workspace(self):
        """Save workspace to file."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if file_path:
                content = self.workspace_text.get("1.0", tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo(
                    "Başarılı", f"Çalışma alanı kaydedildi: {file_path}"
                )
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")

    def load_workspace(self):
        """Load workspace from file."""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.workspace_text.delete("1.0", tk.END)
                self.workspace_text.insert("1.0", content)
                messagebox.showinfo("Başarılı", f"Çalışma alanı yüklendi: {file_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Yükleme hatası: {str(e)}")


def main():
    """Main entry point."""
    try:
        print("🔧 V3 Mühendislik Hesaplayıcı başlatılıyor...")
        root = tk.Tk()
        print("✅ Tkinter root oluşturuldu")

        app = SimpleV3Calculator(root)
        print("✅ V3Calculator oluşturuldu")

        # Force window to appear
        root.update()
        root.deiconify()
        root.lift()
        root.focus_force()
        print("✅ Pencere gösterildi")

        print("🚀 V3 GUI başarıyla başlatıldı!")
        root.mainloop()

    except Exception as e:
        print(f"❌ V3 GUI başlatma hatası: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
