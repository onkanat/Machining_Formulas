#!/usr/bin/env python3
# -*- coding : utf-8 -*-
# V3 GUI - Simple Working Version - Direct Launch
# Autor: Hakan KILIÇASLAN 2025
# flake8: noqa

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font
import json
import math


def main():
    """Direct main function - no class wrapper."""
    try:
        print("🔧 V3 Mühendislik Hesaplayıcı başlatılıyor...")

        # Initialize workspace buffer
        try:
            from workspace_buffer import WorkspaceBuffer

            workspace_buffer = WorkspaceBuffer()
        except ImportError:
            workspace_buffer = None
            print("⚠️ WorkspaceBuffer not available, using basic save/load")

        # Create root window
        root = tk.Tk()
        root.title("🔧 Mühendislik Hesaplayıcı V3 - Direct")
        root.geometry("1200x800")

        # macOS specific window settings
        root.attributes("-alpha", 1.0)  # Full opacity
        root.attributes("-topmost", True)  # Bring to front
        root.lift()  # Raise window
        root.focus_force()  # Force focus

        print("✅ Pencere oluşturuldu")

        # Configure styles
        style = ttk.Style()
        style.theme_use("clam")

        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create paned window
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left panel - Calculations
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Right panel - Workspace
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        # Create notebook for calculations
        notebook = ttk.Notebook(left_frame)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Turning tab
        turning_frame = ttk.Frame(notebook)
        notebook.add(turning_frame, text="Tornalama")

        ttk.Label(
            turning_frame, text="Tornalama Hesaplamaları", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Cutting speed calculation
        cs_frame = ttk.LabelFrame(turning_frame, text="Kesme Hızı")
        cs_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(cs_frame, text="Çap (mm):").pack(anchor="w", padx=5)
        diameter_entry = ttk.Entry(cs_frame, width=20)
        diameter_entry.pack(padx=5, pady=2)
        diameter_entry.insert(0, "100")

        ttk.Label(cs_frame, text="Devir (rpm):").pack(anchor="w", padx=5)
        rpm_entry = ttk.Entry(cs_frame, width=20)
        rpm_entry.pack(padx=5, pady=2)
        rpm_entry.insert(0, "1000")

        def calculate_cutting_speed():
            try:
                d = float(diameter_entry.get())
                n = float(rpm_entry.get())
                vc = (math.pi * d * n) / 1000
                result_label.config(text=f"Sonuç: {vc:.2f} m/dak")
                inject_to_workspace(
                    f"Tornalama Kesme Hızı: {vc:.2f} m/dak (Çap: {d}mm, Devir: {n}rpm)"
                )
            except:
                result_label.config(text="Hata: Geçersiz değerler")

        ttk.Button(cs_frame, text="Hesapla", command=calculate_cutting_speed).pack(
            pady=5
        )
        result_label = ttk.Label(
            cs_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        result_label.pack(pady=5)

        # Milling tab
        milling_frame = ttk.Frame(notebook)
        notebook.add(milling_frame, text="Frezeleme")

        ttk.Label(
            milling_frame, text="Frezeleme Hesaplamaları", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Table feed calculation
        tf_frame = ttk.LabelFrame(milling_frame, text="Tabla İlerlemesi")
        tf_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(tf_frame, text="Diş Başı İlerleme (mm):").pack(anchor="w", padx=5)
        fz_entry = ttk.Entry(tf_frame, width=20)
        fz_entry.pack(padx=5, pady=2)
        fz_entry.insert(0, "0.1")

        ttk.Label(tf_frame, text="Diş Sayısı:").pack(anchor="w", padx=5)
        teeth_entry = ttk.Entry(tf_frame, width=20)
        teeth_entry.pack(padx=5, pady=2)
        teeth_entry.insert(0, "4")

        ttk.Label(tf_frame, text="Devir (rpm):").pack(anchor="w", padx=5)
        milling_rpm_entry = ttk.Entry(tf_frame, width=20)
        milling_rpm_entry.pack(padx=5, pady=2)
        milling_rpm_entry.insert(0, "2000")

        def calculate_table_feed():
            try:
                fz = float(fz_entry.get())
                z = float(teeth_entry.get())
                n = float(milling_rpm_entry.get())
                vf = fz * z * n
                milling_result_label.config(text=f"Sonuç: {vf:.2f} mm/dak")
                inject_to_workspace(
                    f"Frezeleme Tabla İlerlemesi: {vf:.2f} mm/dak (fz: {fz}mm, z: {z}, n: {n}rpm)"
                )
            except:
                milling_result_label.config(text="Hata: Geçersiz değerler")

        ttk.Button(tf_frame, text="Hesapla", command=calculate_table_feed).pack(pady=5)
        milling_result_label = ttk.Label(
            tf_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        milling_result_label.pack(pady=5)

        # Material tab
        material_frame = ttk.Frame(notebook)
        notebook.add(material_frame, text="Malzeme")

        ttk.Label(
            material_frame, text="Malzeme Hesaplamaları", font=("Arial", 12, "bold")
        ).pack(pady=10)

        # Mass calculation
        mass_frame = ttk.LabelFrame(material_frame, text="Kütle Hesabı")
        mass_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(mass_frame, text="Şekil:").pack(anchor="w", padx=5)
        shape_combo = ttk.Combobox(
            mass_frame, values=["Daire", "Dikdörtgen", "Kare", "Boru", "Küre"], width=18
        )
        shape_combo.pack(padx=5, pady=2)
        shape_combo.set("Daire")

        ttk.Label(mass_frame, text="Yoğunluk (g/cm³):").pack(anchor="w", padx=5)
        density_entry = ttk.Entry(mass_frame, width=20)
        density_entry.pack(padx=5, pady=2)
        density_entry.insert(0, "7.85")

        ttk.Label(mass_frame, text="Yarıçap (mm):").pack(anchor="w", padx=5)
        radius_entry = ttk.Entry(mass_frame, width=20)
        radius_entry.pack(padx=5, pady=2)
        radius_entry.insert(0, "10")

        ttk.Label(mass_frame, text="Uzunluk (mm):").pack(anchor="w", padx=5)
        length_entry = ttk.Entry(mass_frame, width=20)
        length_entry.pack(padx=5, pady=2)
        length_entry.insert(0, "100")

        def calculate_mass():
            try:
                density = float(density_entry.get())
                radius = float(radius_entry.get())
                length = float(length_entry.get())
                volume = math.pi * radius**2 * length  # mm³
                volume_cm3 = volume / 1000  # cm³
                mass = volume_cm3 * density
                mass_result_label.config(text=f"Sonuç: {mass:.2f} g")
                inject_to_workspace(
                    f"Malzeme Kütle: {mass:.2f} g (Daire, Yoğunluk: {density}g/cm³)"
                )
            except:
                mass_result_label.config(text="Hata: Geçersiz değerler")

        ttk.Button(mass_frame, text="Hesapla", command=calculate_mass).pack(pady=5)
        mass_result_label = ttk.Label(
            mass_frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        mass_result_label.pack(pady=5)

        # Workspace area
        ttk.Label(right_frame, text="Çalışma Alanı", font=("Arial", 12, "bold")).pack(
            pady=5
        )

        import tkinter.scrolledtext as scrolledtext

        workspace_text = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, width=80, height=30
        )
        workspace_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Add initial content
        initial_content = """Çalışma Alanı

Bu alana hesaplama sonuçlarınızı ekleyebilirsiniz.

Örnek Hesaplamalar:
• Tornalama Kesme Hızı: 314.16 m/dak
• Frezeleme Tabla İlerlemesi: 800.00 mm/dak
• Malzeme Kütle: 246.62 g

Notlar:
• Tüm hesaplamalar otomatik olarak bu alana eklenebilir
• Çalışma alanını kaydedebilir ve yükleyebilirsiniz"""

        workspace_text.insert("1.0", initial_content)

        def inject_to_workspace(text):
            """Inject calculation result to workspace."""
            current_content = workspace_text.get("1.0", tk.END)
            workspace_text.delete("1.0", tk.END)
            workspace_text.insert("1.0", current_content.rstrip() + f"\n• {text}\n")

        def clear_workspace():
            """Clear workspace."""
            workspace_text.delete("1.0", tk.END)
            workspace_text.insert("1.0", "Çalışma Alanı\n\nTemizlendi...")

        # Performance optimization - loading indicators
        loading_window = None

        def show_loading(message="İşlem yapılıyor..."):
            """Show loading indicator."""
            nonlocal loading_window
            try:
                loading_window = tk.Toplevel(root)
                loading_window.title("Yükleniyor")
                loading_window.geometry("300x100")
                loading_window.transient(root)
                loading_window.grab_set()

                # Center the loading window
                loading_window.update_idletasks()
                x = (loading_window.winfo_screenwidth() // 2) - (
                    loading_window.winfo_width() // 2
                )
                y = (loading_window.winfo_screenheight() // 2) - (
                    loading_window.winfo_height() // 2
                )
                loading_window.geometry(f"+{x}+{y}")

                # Loading content
                frame = ttk.Frame(loading_window)
                frame.pack(fill="both", expand=True, padx=20, pady=20)

                # Animated loading text
                loading_label = ttk.Label(frame, text=message, font=("Arial", 10))
                loading_label.pack()

                # Progress bar
                progress = ttk.Progressbar(frame, mode="indeterminate")
                progress.pack(fill="x", pady=10)
                progress.start(10)

                loading_window.protocol(
                    "WM_DELETE_WINDOW", lambda: None
                )  # Prevent closing

            except Exception as e:
                print(f"Loading window error: {e}")

        def hide_loading():
            """Hide loading indicator."""
            nonlocal loading_window
            try:
                if loading_window:
                    loading_window.destroy()
                    loading_window = None
            except:
                pass

        def get_model_suggestion():
            """Get AI model suggestion for workspace content with loading indicator."""
            try:
                current_content = workspace_text.get("1.0", tk.END).strip()
                if not current_content:
                    messagebox.showinfo(
                        "Bilgi", "Önce çalışma alanına bir içerik girin"
                    )
                    return

                # Try to import ollama utilities
                try:
                    from ollama_utils_v2 import (
                        get_available_models,
                        single_chat_request,
                        test_connection,
                    )
                except ImportError:
                    messagebox.showinfo(
                        "Bilgi", "Model öneri sistemi için Ollama gerekli"
                    )
                    return

                # Show loading
                show_loading("Model önerisi alınıyor...")

                # Get available models
                try:
                    models = get_available_models("http://localhost:11434")
                    if not models:
                        hide_loading()
                        messagebox.showinfo("Bilgi", "Kullanılabilir model bulunamadı")
                        return
                except:
                    hide_loading()
                    messagebox.showinfo("Bilgi", "Model bağlantısı kurulamadı")
                    return

                # Prepare prompt for suggestion
                prompt = f"""Bu mühendislik çalışma alanına dayanarak faydalı bir öneri veya tamamlayıcı bilgi sun:

Mevcut içerik:
{current_content}

Lütfen kısaca ve öz olarak:
1. Eksik olabilecek bilgileri öner
2. İlgili hesaplamaları veya formülleri öner
3. Sonraki adımları öner
4. Türkçe cevap ver"""

                # Get suggestion from model
                try:
                    response = single_chat_request(models[0], prompt)
                    hide_loading()
                    if response and response.strip():
                        # Append suggestion to workspace
                        suggestion = (
                            f"\n\n--- 🤖 Model Önerisi ---\n{response.strip()}\n"
                        )
                        workspace_text.insert(tk.END, suggestion)
                        workspace_text.see(tk.END)
                        messagebox.showinfo("Başarılı", "Model önerisi eklendi")
                    else:
                        messagebox.showinfo("Bilgi", "Modelden yanıt alınamadı")
                except Exception as e:
                    hide_loading()
                    messagebox.showinfo("Bilgi", f"Model isteği başarısız: {str(e)}")

            except Exception as e:
                hide_loading()
                messagebox.showerror("Hata", f"Öneri alma hatası: {str(e)}")

        def enhanced_save_workspace():
            """Enhanced save with loading indicator."""
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[
                        ("Text files", "*.txt"),
                        ("JSON files", "*.json"),
                        ("All files", "*.*"),
                    ],
                )
                if file_path:
                    show_loading("Çalışma alanı kaydediliyor...")

                    current_content = workspace_text.get("1.0", tk.END).strip()

                    if file_path.endswith(".json") and workspace_buffer:
                        # Enhanced save with workspace buffer
                        workspace_buffer.set_content(
                            current_content, "user", "Workspace saved"
                        )
                        success = workspace_buffer.save_to_file(file_path)
                    else:
                        # Basic text save
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(current_content)
                        success = True

                    hide_loading()

                    if success:
                        messagebox.showinfo(
                            "Başarılı", f"Çalışma alanı kaydedildi: {file_path}"
                        )
                    else:
                        messagebox.showerror("Hata", "Kaydetme başarısız oldu")
            except Exception as e:
                hide_loading()
                messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")

        def enhanced_load_workspace():
            """Enhanced load with loading indicator."""
            try:
                file_path = filedialog.askopenfilename(
                    filetypes=[
                        ("Text files", "*.txt"),
                        ("JSON files", "*.json"),
                        ("All files", "*.*"),
                    ]
                )
                if file_path:
                    show_loading("Çalışma alanı yükleniyor...")

                    if file_path.endswith(".json") and workspace_buffer:
                        # Enhanced load with workspace buffer
                        success = workspace_buffer.load_from_file(file_path)
                        if success:
                            content = workspace_buffer.get_content()
                        else:
                            hide_loading()
                            messagebox.showerror("Hata", "Yükleme başarısız oldu")
                            return
                    else:
                        # Basic text load
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        if workspace_buffer:
                            workspace_buffer.set_content(
                                content, "user", "Workspace loaded"
                            )

                    workspace_text.delete("1.0", tk.END)
                    workspace_text.insert("1.0", content)
                    hide_loading()
                    messagebox.showinfo(
                        "Başarılı", f"Çalışma alanı yüklendi: {file_path}"
                    )
            except Exception as e:
                hide_loading()
                messagebox.showerror("Hata", f"Yükleme hatası: {str(e)}")

        # Performance optimization - debounce rapid calculations
        calculation_timer = None

        def debounce_calculation(calc_func, delay=500):
            """Debounce rapid calculations to improve performance."""
            nonlocal calculation_timer

            def cancel_timer():
                nonlocal calculation_timer
                if calculation_timer:
                    root.after_cancel(calculation_timer)
                    calculation_timer = None

            cancel_timer()
            calculation_timer = root.after(delay, calc_func)

        # Update save/load functions to use enhanced versions
        def save_workspace():
            """Save workspace with loading indicator."""
            enhanced_save_workspace()

        def load_workspace():
            """Load workspace with loading indicator."""
            enhanced_load_workspace()

        # Control buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text="Temizle", command=clear_workspace).pack(
            side="left", padx=2
        )
        ttk.Button(button_frame, text="Kaydet", command=save_workspace).pack(
            side="left", padx=2
        )
        ttk.Button(button_frame, text="Yükle", command=load_workspace).pack(
            side="left", padx=2
        )
        ttk.Button(button_frame, text="🤖 Öneri", command=get_model_suggestion).pack(
            side="left", padx=2
        )

        # Keyboard shortcuts and accessibility
        def setup_keyboard_shortcuts():
            """Setup keyboard shortcuts for accessibility."""

            # File operations
            root.bind("<Control-s>", lambda e: save_workspace())
            root.bind("<Control-o>", lambda e: load_workspace())
            root.bind("<Control-n>", lambda e: clear_workspace())

            # Model suggestion
            root.bind("<Control-m>", lambda e: get_model_suggestion())

            # Tab navigation
            root.bind("<Control-Tab>", lambda e: focus_next_widget())
            root.bind("<Control-Shift-Tab>", lambda e: focus_prev_widget())

            # Quick calculations (Ctrl+1, Ctrl+2, Ctrl+3 for tabs)
            root.bind("<Control-1>", lambda e: notebook.select(0))  # Turning
            root.bind("<Control-2>", lambda e: notebook.select(1))  # Milling
            root.bind("<Control-3>", lambda e: notebook.select(2))  # Material
            root.bind("<Control-4>", lambda e: notebook.select(3))  # Workspace

            # Help
            root.bind("<F1>", lambda e: show_help())
            root.bind("<Control-h>", lambda e: show_help())

            # Exit
            root.bind("<Control-q>", lambda e: root.quit())
            root.bind("<Escape>", lambda e: root.quit())

        def focus_next_widget(event=None):
            """Focus next widget in tab order."""
            try:
                if event and event.widget:
                    event.widget.tk_focusNext().focus_set()
            except:
                pass
            return "break"

        def focus_prev_widget(event=None):
            """Focus previous widget in tab order."""
            try:
                if event and event.widget:
                    event.widget.tk_focusPrev().focus_set()
            except:
                pass
            return "break"

        def show_help():
            """Show help dialog with keyboard shortcuts."""
            help_text = """
🔧 Mühendislik Hesaplayıcı V3 - Kısayol Tuşları

📁 Dosya İşlemleri:
  Ctrl+S - Çalışma alanını kaydet
  Ctrl+O - Çalışma alanını yükle
  Ctrl+N - Çalışma alanını temizle

🤖 Model İşlemleri:
  Ctrl+M - Model önerisi al

📑 Sekme Geçişi:
  Ctrl+1 - Torna hesaplamaları
  Ctrl+2 - Freze hesaplamaları
  Ctrl+3 - Malzeme hesaplamaları
  Ctrl+4 - Çalışma alanı

🖱️ Navigasyon:
  Ctrl+Tab - Sonraki widget
  Ctrl+Shift+Tab - Önceki widget
  Tab - Widget içinde gezinme

❓ Yardım:
  F1 veya Ctrl+H - Bu yardım penceresi
  
🚪 Çıkış:
  Ctrl+Q veya Escape - Uygulamadan çık

📝 Hesaplamalar:
  Enter - Aktif hesaplamayı çalıştır
  Ctrl+Enter - Sonucu çalışma alanına ekle
            """

            help_window = tk.Toplevel(root)
            help_window.title("Yardım - Kısayol Tuşları")
            help_window.geometry("500x600")
            help_window.transient(root)
            help_window.grab_set()

            text_widget = tk.Text(help_window, wrap="word", padx=10, pady=10)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", help_text)
            text_widget.config(state="disabled")

            close_btn = ttk.Button(
                help_window, text="Kapat", command=help_window.destroy
            )
            close_btn.pack(pady=10)

            # Center the help window
            help_window.update_idletasks()
            x = (help_window.winfo_screenwidth() // 2) - (
                help_window.winfo_width() // 2
            )
            y = (help_window.winfo_screenheight() // 2) - (
                help_window.winfo_height() // 2
            )
            help_window.geometry(f"+{x}+{y}")

        def setup_accessibility():
            """Setup accessibility improvements."""

            # High contrast mode support
            try:
                root.option_add("*TCombobox*Listbox.selectBackground", "#0078d4")
                root.option_add("*TCombobox*Listbox.selectForeground", "white")
            except:
                pass

            # Larger fonts for better readability
            try:
                default_font = font.nametofont("TkDefaultFont")
                default_font.configure(size=10)

                text_font = font.nametofont("TkTextFont")
                text_font.configure(size=10)
            except:
                pass

            # Focus indicators
            style = ttk.Style()
            style.configure("TEntry", focuscolor="blue")
            style.configure("TCombobox", focuscolor="blue")
            style.configure("TButton", focuscolor="blue")

        # Enhanced enter key handling for calculations
        def bind_enter_keys():
            """Bind Enter keys for quick calculations."""

            # Turning calculations - bind Enter to calculate button
            diameter_entry.bind("<Return>", lambda e: calculate_cutting_speed())
            rpm_entry.bind("<Return>", lambda e: calculate_cutting_speed())

            # Milling calculations - bind Enter to calculate buttons
            fz_entry.bind("<Return>", lambda e: calculate_table_feed())
            teeth_entry.bind("<Return>", lambda e: calculate_table_feed())
            milling_rpm_entry.bind("<Return>", lambda e: calculate_table_feed())

            # Material calculations
            density_entry.bind("<Return>", lambda e: calculate_mass())
            radius_entry.bind("<Return>", lambda e: calculate_mass())
            length_entry.bind("<Return>", lambda e: calculate_mass())

            # Workspace text widget - Ctrl+Enter for model suggestion
            workspace_text.bind("<Control-Return>", lambda e: get_model_suggestion())

        # Setup all enhancements
        setup_keyboard_shortcuts()
        setup_accessibility()
        bind_enter_keys()

        # Set initial focus
        diameter_entry.focus_set()

        # Remove topmost after showing
        root.after(1000, lambda: root.attributes("-topmost", False))

        # Force window update
        root.update_idletasks()
        root.deiconify()
        root.lift()
        root.focus_force()

        print("✅ V3 GUI başarıyla oluşturuldu!")
        print("⌨️  Kısayol tuşları eklendi (F1 için yardım)")
        print("♿ Erişilebilirlik özellikleri aktif")
        print("🚀 Başlatılıyor...")

        # Start GUI
        root.mainloop()

    except Exception as e:
        print(f"❌ V3 GUI başlatma hatası: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
