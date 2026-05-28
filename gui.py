import customtkinter as ctk
from tkinter import ttk
import threading
from PIL import Image
import asyncio
import json
import os
import sys
import pandas as pd
import urllib.request
import time
from main import run_screener_async, send_telegram_alert

BG_COLOR = "#0A0A0A"
CARD_BG = "#121212"
CYAN = "#00A8FF"
NEON_GREEN = "#00FF9D"
NEON_ORANGE = "#FF4500"
TEXT_MAIN = "#E2E8F0"
TEXT_SUB = "#64748B"

CURRENT_VERSION = "1.0"

ctk.set_appearance_mode("dark")

class AltcoinSelectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.geometry("1100x750")
        self.title("AltcoinSelector - Premium Intelligence Terminal")
        self.configure(fg_color=BG_COLOR)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.brand_frame.pack(pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.brand_frame, 
            text="ALTCOIN SELECTOR", 
            font=("Montserrat", 40, "bold"),
            text_color="white"
        )
        self.title_label.pack()
        
        self.premium_tag = ctk.CTkLabel(
            self.brand_frame, 
            text="Premium Edition", 
            font=("Playfair Display", 18, "italic"),
            text_color=CYAN
        )
        self.premium_tag.pack(pady=0)

        self.tabview = ctk.CTkTabview(
            self, 
            width=1050, 
            height=600, 
            fg_color=CARD_BG,
            segmented_button_selected_color=CYAN,
            segmented_button_selected_hover_color="#00CCCC",
            segmented_button_unselected_hover_color="#1F1F1F",
            text_color="white"
        )
        self.tabview.pack(padx=25, pady=10)
        
        self.tabview.add("Market Screener")
        self.tabview.add("Our Recommendations 🎯")
        self.tabview.add("How to Use")
        
        self.setup_styles()
        self.setup_screener_tab()
        self.setup_recommendation_tab()
        self.setup_guide_tab()
        
        self.load_config()
        self.after(800, self.start_scan)
        self.check_for_updates()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure(
            "Treeview", 
            background=CARD_BG, 
            foreground=TEXT_MAIN, 
            rowheight=35, 
            fieldbackground=CARD_BG, 
            borderwidth=0, 
            font=("Consolas", 11)
        )
        self.style.map('Treeview', background=[('selected', '#1f538d')])
        self.style.configure(
            "Treeview.Heading", 
            background="#1f538d", 
            foreground="white", 
            font=('Arial', 11, 'bold'), 
            borderwidth=0
        )

    def setup_screener_tab(self):
        self.ctrl = ctk.CTkFrame(self.tabview.tab("Market Screener"), fg_color="transparent")
        self.ctrl.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(self.ctrl, text="TIMEFRAME:", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        self.tf_combo = ctk.CTkComboBox(self.ctrl, values=["15m", "1H", "4H", "1D"], width=90, border_color=CYAN, button_color=CYAN)
        self.tf_combo.set("1H")
        self.tf_combo.pack(side="left", padx=10)
        
        ctk.CTkLabel(self.ctrl, text="SCOPE:", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        self.top_slider = ctk.CTkSlider(self.ctrl, from_=10, to=300, number_of_steps=29, width=180, button_color=CYAN, progress_color=CYAN, command=self.update_slider_label)
        self.top_slider.pack(side="left", padx=10)
        
        self.top_val_label = ctk.CTkLabel(self.ctrl, text="50", font=("Consolas", 14, "bold"), text_color=CYAN)
        self.top_val_label.pack(side="left")
        
        self.scan_btn = ctk.CTkButton(self.ctrl, text="SCAN", command=self.start_scan, font=("Arial", 16, "bold"), text_color="white", fg_color="#00BFFF", hover_color="#0099CC")
        self.scan_btn.pack(side="right", padx=10)

        try:
            tg_icon = ctk.CTkImage(dark_image=Image.open("telegram.png"), size=(30, 30))
        except Exception:
            tg_icon = None # Nếu không tìm thấy file ảnh thì bỏ qua
            
        # 2. Tạo nút (Bỏ chữ TG đi, nhét image=tg_icon vào)
        self.tg_btn = ctk.CTkButton(
            self.ctrl, 
            text="ALERTS",
            image=tg_icon,
            command=self.open_tg_settings, 
            font=("Arial", 12, "bold"), 
            fg_color="#8A2BE2", 
            width=100
        )
        self.tg_btn.pack(side="right", padx=10)
        
        self.auto_switch = ctk.CTkSwitch(self.ctrl, text="AUTO SCAN", font=("Arial", 11, "bold"), progress_color=NEON_GREEN, command=self.toggle_auto_loop)
        self.auto_switch.pack(side="right", padx=20)
        self.auto_job = None

        self.progress_bar = ctk.CTkProgressBar(self.tabview.tab("Market Screener"), width=800, progress_color=CYAN)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        
        self.status_label = ctk.CTkLabel(self.tabview.tab("Market Screener"), text="SYSTEM READY", font=("Consolas", 12), text_color=TEXT_SUB)
        self.status_label.pack()
        
        cols = ("NO", "SYMBOL", "PRICE", "24H CHG", "VOLUME", "BANDWIDTH", "RSI", "SIGNAL")
        self.tree = ttk.Treeview(self.tabview.tab("Market Screener"), columns=cols, show="headings", height=13)
        
        wds = [45, 130, 110, 110, 130, 130, 80, 170]
        for c, w in zip(cols, wds):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
            
        self.tree.tag_configure('Bullish Breakout', foreground=NEON_GREEN)
        self.tree.tag_configure('Bearish Breakout', foreground=NEON_ORANGE)
        self.tree.tag_configure('Squeezing', foreground=CYAN)
        self.tree.pack(pady=15, padx=20, fill="both", expand=True)

    def setup_recommendation_tab(self):
        self.rec_title = ctk.CTkLabel(self.tabview.tab("Our Recommendations 🎯"), text="TOP 10 CRYPTO RECOMMENDATIONS", font=("Arial", 22, "bold"), text_color=CYAN)
        self.rec_title.pack(pady=(20, 5))
        
        cols = ("RANK", "SYMBOL", "PRICE", "24H CHG", "VOLUME", "BANDWIDTH", "RSI", "SIGNAL", "STRATEGY")
        self.rec_tree = ttk.Treeview(self.tabview.tab("Our Recommendations 🎯"), columns=cols, show="headings", height=11)
        
        wds = [50, 120, 110, 90, 110, 110, 80, 140, 180]
        for c, w in zip(cols, wds):
            self.rec_tree.heading(c, text=c)
            self.rec_tree.column(c, width=w, anchor="center")
            
        self.rec_tree.tag_configure('Bullish Breakout', foreground=NEON_GREEN)
        self.rec_tree.tag_configure('Bearish Breakout', foreground=NEON_ORANGE)
        self.rec_tree.tag_configure('Squeezing', foreground=CYAN)
        self.rec_tree.pack(pady=20, padx=20, fill="both", expand=True)

    def setup_guide_tab(self):
        guide_text = """
QUICK START GUIDE - ALTCOIN SELECTOR
-------------------------------------------------------------------------------
The AltcoinSelector utilizes Bollinger Squeeze mechanics to identify high-tension 
market phases. When Bandwidth drops below 5%, the spring is coiled for a move.

⚙️ CONTROL PANEL:
* TIMEFRAME : Choose your play. 15m (Scalping), 1H (Day Trading), 4H/1D (Swing).
* SCOPE     : The number of Top Market-Cap coins to scan (e.g., Top 50).
* AUTO SCAN : Hands-free mode. Refreshes data and updates UI every 15 minutes.
* ALERTS    : Connect Telegram to get breakout signals directly to your phone.
  [!] NOTE  : Auto Scan & Telegram Alerts ONLY work while the app is OPEN.

🚦 SIGNAL LIGHTS (MARKET SCREENER):
* [BLUE]   SQUEEZING        : Volatility < 5%. Wait for the breakout.
* [GREEN]  BULLISH BREAKOUT : Squeeze + RSI > 60. Upward momentum.
* [RED] BEARISH BREAKOUT : Squeeze + RSI < 40. Downward pressure.

🎯 OUR RECOMMENDATIONS (STRATEGY TIERS):
* Tier 1 (Holy Grail) : Breakout + 3 Timeframes Aligned + Huge Volume.
* Tier 2 (Shark Vol)  : Breakout + Smart Money Volume (>2.5x moving average).
* Tier 3 (Trend)      : Breakout aligned with the Macro Trend.
* Tier 4 (Confluence) : Tightest squeezes waiting for a catalyst volume.

⚔️ EXECUTION STRATEGY:
1. SET TIMEFRAME: 15m/1H for Day Trading | 4H/1D for Swing Trading.
2. SCAN: Run the engine and check 'Our recommendations' for the current most potential crypto.
3. VERIFY: Open the chart to confirm the Darvas Box / Consolidation zone.
4. EXECUTE: Enter ONLY on a firm candle close outside the squeeze boundary.
5. PROTECT: Place Stop-Loss at the opposite Bollinger Band limit.
-------------------------------------------------------------------------------
*For deep-dive technical setups, please refer to the attached PDF Manual.*
"""
        self.guide_box = ctk.CTkTextbox(self.tabview.tab("How to Use"), width=900, height=480, font=("Consolas", 14), fg_color="#0F0F0F", text_color=TEXT_MAIN)
        self.guide_box.pack(pady=25)
        self.guide_box.insert("0.0", guide_text)
        self.guide_box.configure(state="disabled")

    def open_tg_settings(self):
        tg_win = ctk.CTkToplevel(self)
        tg_win.geometry("550x420")
        tg_win.title("Telegram Bot Configuration")
        tg_win.attributes("-topmost", True)
        tg_win.lift()

        ctk.CTkLabel(tg_win, text="TELEGRAM ALERTS SETUP", font=("Montserrat", 18, "bold"), text_color=CYAN).pack(pady=(20, 10))
        
        ctk.CTkLabel(tg_win, text="Bot Token (From @BotFather):").pack(anchor="w", padx=30)
        token_entry = ctk.CTkEntry(tg_win, width=490, fg_color="#1A1A1A")
        token_entry.pack(pady=(0, 15), padx=30)

        ctk.CTkLabel(tg_win, text="Chat ID (From @userinfobot):").pack(anchor="w", padx=30)
        chatid_entry = ctk.CTkEntry(tg_win, width=490, fg_color="#1A1A1A")
        chatid_entry.pack(pady=(0, 15), padx=30)

        # --- KHU VỰC CHECKBOX LỌC TIER ---
        ctk.CTkLabel(tg_win, text="Signal Filters (Select Tiers to receive):", font=("Arial", 12, "bold")).pack(anchor="w", padx=30)
        
        cb_frame = ctk.CTkFrame(tg_win, fg_color="transparent")
        cb_frame.pack(fill="x", padx=30, pady=(5, 20))
        
        # Khai báo biến lưu trạng thái checkbox
        t1_var = ctk.IntVar(value=1)
        t2_var = ctk.IntVar(value=1)
        t3_var = ctk.IntVar(value=0) # Mặc định tắt Tier 3 để chống spam

        cb1 = ctk.CTkCheckBox(cb_frame, text="Tier 1 (Holy Grail)", variable=t1_var, fg_color=CYAN, text_color="white")
        cb1.pack(side="left", padx=(0, 15))
        cb2 = ctk.CTkCheckBox(cb_frame, text="Tier 2 (Shark Vol)", variable=t2_var, fg_color=CYAN, text_color="white")
        cb2.pack(side="left", padx=(0, 15))
        cb3 = ctk.CTkCheckBox(cb_frame, text="Tier 3 (Best 3 Trend Aligned)", variable=t3_var, fg_color=CYAN, text_color="white")
        cb3.pack(side="left")

        # Đọc dữ liệu cũ đắp lên UI
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                if "tg_token" in cfg: token_entry.insert(0, cfg["tg_token"])
                if "tg_chat_id" in cfg: chatid_entry.insert(0, cfg["tg_chat_id"])
                if "tg_tier1" in cfg: t1_var.set(cfg["tg_tier1"])
                if "tg_tier2" in cfg: t2_var.set(cfg["tg_tier2"])
                if "tg_tier3" in cfg: t3_var.set(cfg["tg_tier3"])
        except: pass

        def save_tg():
            try:
                with open("config.json", "r") as f: cfg = json.load(f)
            except: cfg = {}
            
            cfg["tg_token"] = token_entry.get().strip()
            cfg["tg_chat_id"] = chatid_entry.get().strip()
            # Lưu trạng thái 3 cái nút tick
            cfg["tg_tier1"] = t1_var.get()
            cfg["tg_tier2"] = t2_var.get()
            cfg["tg_tier3"] = t3_var.get()
            
            with open("config.json", "w") as f: json.dump(cfg, f, indent=4)
            tg_win.destroy()

        ctk.CTkButton(tg_win, text="SAVE CONFIGURATION", command=save_tg, fg_color=CYAN, text_color="black", font=("Arial", 12, "bold")).pack(pady=10)


    def toggle_auto_loop(self):
        if self.auto_switch.get() == 1:
            self.status_label.configure(text="AUTO SCAN ACTIVATED - STARTING ENGINE")
            if self.scan_btn.cget("text") == "SCAN":
                self.start_scan()
        else:
            # Nếu tắt đi thì vẫn giữ lại giờ update cũ cho chuyên nghiệp
            last_time = getattr(self, 'last_update_time', 'N/A')
            self.status_label.configure(text=f"Last Updated: {last_time}  |  AUTO SCAN DEACTIVATED")
            if self.auto_job:
                self.after_cancel(self.auto_job)
                self.auto_job = None

    def tick_timer(self):
        # Nếu công tắc bị tắt giữa chừng thì dừng đếm ngược
        if self.auto_switch.get() == 0:
            return 
            
        if getattr(self, 'minutes_left', 0) > 0:
            # Cập nhật giao diện đếm ngược từng phút
            self.status_label.configure(text=f"Last Updated: {self.last_update_time}  |  Next scan in {self.minutes_left} minute(s)...")
            self.minutes_left -= 1
            # Hẹn 60,000 mili-giây (1 phút) sau gọi lại chính hàm này
            self.auto_job = self.after(60000, self.tick_timer)
        else:
            # Hết giờ thì tự động quét
            self.status_label.configure(text="AUTO SCAN ACTIVATED - STARTING ENGINE...")
            self.start_scan()            
        
    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    cfg = json.load(f)
                    if "timeframe" in cfg: self.tf_combo.set(cfg["timeframe"])
                    if "top_n" in cfg:
                        v = float(cfg["top_n"])
                        self.top_slider.set(v)
                        self.top_val_label.configure(text=str(int(v)))
                    if cfg.get("auto_alert") == 1:
                        self.auto_switch.select()
            except: pass

    def check_for_updates(self):
        def worker():
            # Github raw file version.txt link
            url = "https://raw.githubusercontent.com/hexadeci/public-cdn/main/version.txt"
            try:
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    latest_version = response.read().decode('utf-8').strip()
                
                
                if float(latest_version) > float(CURRENT_VERSION):
                    
                    self.after(2000, lambda: self.show_update_popup(latest_version))
            except:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def show_update_popup(self, latest_version):
        popup = ctk.CTkToplevel(self)
        popup.geometry("400x200")
        popup.title("Update Available")
        popup.attributes("-topmost", True)
        
        popup.lift()
        
        lbl = ctk.CTkLabel(popup, text=f"⚠️ NEW UPDATE AVAILABLE\n\nVersion v{latest_version} is now active.\nYour current version is v{CURRENT_VERSION}.", font=("Arial", 13, "bold"))
        lbl.pack(pady=30)
        
        btn = ctk.CTkButton(popup, text="DOWNLOAD NOW", fg_color=CYAN, text_color="black", font=("Arial", 12, "bold"), command=lambda: [os.system("start https://gumroad.com"), popup.destroy()])
        btn.pack()

    def save_config(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    cfg = json.load(f)
            else:
                cfg = {}
                
            cfg["timeframe"] = self.tf_combo.get()
            cfg["top_n"] = int(self.top_slider.get())
            cfg["auto_alert"] = self.auto_switch.get()
            
            with open("config.json", "w") as f:
                json.dump(cfg, f, indent=4)
        except: pass

    def on_closing(self):
        self.save_config()
        self.destroy()

    def update_slider_label(self, value):
        self.top_val_label.configure(text=str(int(value)))

    def update_progress(self, current, total, symbol):
        progress = current / total
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"ANALYZING ASSET: {symbol}... [{current}/{total}]")

    def format_volume(self, vol):
        if vol >= 1_000_000: return f"${vol/1_000_000:.2f}M"
        if vol >= 1_000: return f"${vol/1_000:.2f}K"
        return f"${vol:.0f}"

    def start_scan(self):
        if getattr(self, 'auto_job', None):
            self.after_cancel(self.auto_job)
            self.auto_job = None

        self.scan_btn.configure(state="disabled", text="SCANNING...")
        for i in self.tree.get_children(): self.tree.delete(i)
        for i in self.rec_tree.get_children(): self.rec_tree.delete(i)
        threading.Thread(target=self.run_task, args=(int(self.top_slider.get()), self.tf_combo.get()), daemon=True).start()

    def run_task(self, top_n, tf):
        if sys.platform.startswith('win'): asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        try:
            df = asyncio.run(run_screener_async(top_n, tf, self.update_progress))
            if not df.empty:
                prime = []
                for i, row in df.iterrows():
                    chg = f"+{row['Change']:.2f}%" if row['Change'] > 0 else f"{row['Change']:.2f}%"
                    sig = row['Signal']
                    self.tree.insert("", "end", values=(i+1, row['Symbol'], f"{row['Price']}", chg, self.format_volume(row['Volume']), f"{row['Bandwidth']}%", row['RSI'], sig), tags=(sig,))
                
                    if sig in ["Bullish Breakout", "Bearish Breakout", "Squeezing"]: prime.append(row)
                
                if prime:
                    rec_df = pd.DataFrame(prime)

                    tier1 = rec_df[rec_df['Tier'] == 1].sort_values(by='Score', ascending=False)
                    tier2 = rec_df[rec_df['Tier'] == 2].sort_values(by='Score', ascending=False)
                    tier3 = rec_df[rec_df['Tier'] == 3].sort_values(by='Score', ascending=False)
                    tier4 = rec_df[rec_df['Tier'] == 4].sort_values(by='Volume', ascending=False)

                    waterfall_df = pd.concat([tier1, tier2, tier3, tier4])

                    final_rec = waterfall_df.head(10)

                    vip_df = final_rec[final_rec['Tier'].isin([1, 2, 3])]
                    
                    if not vip_df.empty:
                        # 1. Khám xét file config xem khách hàng bật cái gì
                        try:
                            with open("config.json", "r") as f:
                                cfg = json.load(f)
                                t1_on = cfg.get("tg_tier1", 1) # Nếu không thấy thì auto bật
                                t2_on = cfg.get("tg_tier2", 1)
                                t3_on = cfg.get("tg_tier3", 0) # Auto tắt Tier 3
                        except:
                            t1_on, t2_on, t3_on = 1, 1, 0
                            
                        # 2. Xếp đồ ra mâm tùy theo order của khách
                        alert_pieces = []
                        if t1_on == 1: 
                            alert_pieces.append(vip_df[vip_df['Tier'] == 1])
                        if t2_on == 1: 
                            alert_pieces.append(vip_df[vip_df['Tier'] == 2])
                        if t3_on == 1: 
                            alert_pieces.append(vip_df[vip_df['Tier'] == 3].head(3)) # Chốt chặn Max 3 con
                            
                        # 3. Gom lại và gửi đi
                        if alert_pieces:
                            final_alert = pd.concat(alert_pieces)
                            if not final_alert.empty:
                                final_alert = final_alert.sort_values(by='Tier')
                                
                                alert_msg = f"💎 *PREMIUM SIGNALS [{tf}]*\n----------------------------------\n"
                                for _, row in final_alert.iterrows():
                                    emoji = "🟢 LONG" if "Bullish" in row['Signal'] else "🔴 SHORT"
                                    tier_num = row['Tier']
                                    if tier_num == 1: strategy = "Tier 1: Holy Grail"
                                    elif tier_num == 2: strategy = "Tier 2: Shark Volume"
                                    else: strategy = "Tier 3: Trend Aligned"
                                    
                                    alert_msg += f"{emoji} *{row['Symbol']}* _({strategy})_\n"
                                    alert_msg += f"Price: `{row['Price']}` | RSI: `{row['RSI']}`\n"
                                    alert_msg += f"Bandwidth: `{row['Bandwidth']}%`\n\n"
                                    
                                threading.Thread(target=send_telegram_alert, args=(alert_msg,), daemon=True).start()

                    for i, row in final_rec.reset_index().iterrows():
                        chg = f"+{row['Change']:.2f}%" if row['Change'] > 0 else f"{row['Change']:.2f}%"
                        sig = row['Signal']
                        tier_num = row['Tier']
                        if tier_num == 1: strategy = "Tier 1: Holy Grail (3TF)"
                        elif tier_num == 2: strategy = "Tier 2: Shark Volume"
                        elif tier_num == 3: strategy = "Tier 3: Trend Aligned"
                        else: strategy = "Tier 4: Confluence"
                        self.rec_tree.insert("", "end", values=(i+1, row['Symbol'], f"{row['Price']}", chg, self.format_volume(row['Volume']), f"{row['Bandwidth']}%", row['RSI'], sig, strategy), tags=(sig,))
                self.status_label.configure(text="SCAN COMPLETED - ANALYSIS IDLE")
            else: self.status_label.configure(text="ERROR: DATA RETRIEVAL FAILED")
        except Exception as e: self.status_label.configure(text=f"CRITICAL ERROR: {str(e)}")
        finally:
            self.scan_btn.configure(state="normal", text="SCAN", text_color="white", font=("Arial", 16, "bold"))
            self.progress_bar.set(0)
            
            # Ghi nhận thời điểm quét xong (Ví dụ: 14:30:00)
            self.last_update_time = time.strftime("%H:%M:%S")
            
            # Kích hoạt đếm ngược hoặc chỉ hiện giờ
            if self.auto_switch.get() == 1:
                self.minutes_left = 15  # Cài đặt 15 phút/lần
                self.tick_timer()       # Bắt đầu nhịp gõ đếm ngược
            else:
                self.status_label.configure(text=f"Last Updated: {self.last_update_time}")

if __name__ == "__main__":
    app = AltcoinSelectorApp()
    app.mainloop()