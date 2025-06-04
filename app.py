import streamlit as st
import json
import os
import base64
import smtplib
from email.message import EmailMessage
import glob

# Determine base path
base_path = os.path.dirname(os.path.abspath(__file__))

# Paths
json_files_folder = os.path.join(base_path, "machine_data")
images_folder = os.path.join(base_path, "images")
downloads_folder = os.path.join(base_path, "downloads")
logo_path = os.path.join(base_path, "logo.png")
email_config_path = os.path.join(base_path, "email_config.json")

def get_machine_files():
    """Get all JSON files from the machine_data folder"""
    if not os.path.exists(json_files_folder):
        return {}
    
    machine_files = {}
    json_pattern = os.path.join(json_files_folder, "*.json")
    
    for json_file in glob.glob(json_pattern):
        filename = os.path.basename(json_file)
        machine_name = os.path.splitext(filename)[0]
        display_name = format_machine_name(machine_name)
        machine_files[display_name] = json_file
    
    return machine_files

def format_machine_name(filename):
    """Format filename to display name"""
    formatted = filename.upper()
    import re
    formatted = re.sub(r'(\D)(\d)', r'\1 \2', formatted)
    return formatted

def load_machine_data(json_file_path):
    """Load troubleshooting data from selected machine JSON file"""
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
        return data, True, "✔️ Machine data loaded successfully"
    except Exception as e:
        return None, False, f"❌ Error loading data: {e}"

def send_email(subject, body, machine_name=None):
    """Send email function (same as original)"""
    try:
        with open(email_config_path, "r") as f:
            email_config = json.load(f)

        from_email = email_config["EMAIL_ADDRESS"]
        to_email = email_config["TO_EMAIL"]
        smtp_server = email_config.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = email_config.get("SMTP_PORT", 587)
        password = os.getenv("EMAIL_PASSWORD")

        if not password:
            st.error("❌ EMAIL_PASSWORD environment variable is not set.")
            return False

        if machine_name:
            body = f"Machine: {machine_name}\n\n{body}"

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(from_email, password)
            smtp.send_message(msg)

        return True
    except Exception as e:
        st.error(f"❌ Email failed: {e}")
        return False

def display_steps(steps):
    """Display troubleshooting steps (same as original)"""
    for step in steps:
        if isinstance(step, dict):
            st.markdown(f"- {step.get('step', '')}")
            if "image" in step:
                image_path = os.path.join(images_folder, step["image"])
                if os.path.exists(image_path):
                    st.image(image_path, use_container_width=False, width=600)
                else:
                    st.warning(f"⚠️ Image not found: {step['image']}")
        else:
            st.markdown(f"- {step}")

def main():
    st.set_page_config(
        page_title="Predictive ATE Maintenance", 
        page_icon="🔮", 
        layout="wide"
    )
    # Add logo in the top-right corner
    logo_base64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
           logo_bytes = f.read()
        logo_base64 = base64.b64encode(logo_bytes).decode()

    if logo_base64:
       st.markdown(
           f"""
           <div style="position: absolute; top: 10px; right: 10px;">
            <img src="data:image/png;base64,{logo_base64}" width="100">
           </div>
            """,
            unsafe_allow_html=True,
       )
    # Header
    st.markdown("# 🛠️ ATE Maintenance System")
    st.markdown("*Equipment Health Monitoring & Troubleshooting*")
    
    # Sidebar for navigation
    st.sidebar.title("🚀 Navigation")
    page = st.sidebar.selectbox("Select View", [
        "🛠️ Manual Troubleshooting",
        "📧 Support & Alerts"
    ])

    # Machine Selection
    machine_files = get_machine_files()
    if not machine_files:
        st.error("❌ No machine JSON files found")
        return

    selected_machine = st.sidebar.selectbox("🏭 Select Machine", list(machine_files.keys()))
    
    # Load machine data
    selected_json_path = machine_files[selected_machine]
    troubleshooting_data, load_success, load_message = load_machine_data(selected_json_path)
    
    if not load_success:
        st.error(load_message)
        return
# Manual Troubleshooting Page
    if page == "🛠️ Manual Troubleshooting":
        st.header(f"🛠️ Manual Troubleshooting - {selected_machine}")
        
        # ... your existing troubleshooting UI code here ...
        troubleshooting_categories = {k: v for k, v in troubleshooting_data.items() if k != "Support_Documents"}
        main_option = st.selectbox("Select a category:", list(troubleshooting_categories.keys()))
        
        if isinstance(troubleshooting_categories[main_option], list):
            st.subheader(f"{selected_machine} → {main_option}")
            display_steps(troubleshooting_categories[main_option])
        else:
            sub_options = list(troubleshooting_categories[main_option].keys())
            sub_option = st.selectbox("Select a specific issue:", sub_options)
            st.subheader(f"{selected_machine} → {main_option} → {sub_option}")
            display_steps(troubleshooting_categories[main_option][sub_option])
        
        # Support Documents section
        st.markdown("---")
        st.markdown("### 📥 Download Support Files")
        if "Support_Documents" in troubleshooting_data:
            doc_categories = list(troubleshooting_data["Support_Documents"].keys())
            col1, col2 = st.columns([1, 3])
            
            with col1:
                selected_category = st.radio("Categories", doc_categories)
            
            with col2:
                category_docs = troubleshooting_data["Support_Documents"][selected_category]
                if category_docs:
                    selected_doc = st.selectbox("Select document:", category_docs)
                    download_file_path = os.path.join(downloads_folder, selected_doc)
                    if os.path.exists(download_file_path):
                        with open(download_file_path, "rb") as file:
                            st.download_button(
                                label=f"📥 Download {selected_doc}",
                                data=file,
                                file_name=selected_doc,
                                mime="application/octet-stream"
                            )
                    else:
                        st.warning(f"⚠️ File not found: {selected_doc}")
    
    # Support & Alerts Page (Email Sending)
    elif page == "📧 Support & Alerts":
        st.header("📧 Support & Alerts - Send Custom Message")
     
        st.markdown("#### ✉️ Gmail Setup Instructions")
        st.markdown("""
         To send emails, you must use a **Gmail App Password** (not your Gmail login password).
     
         👉 [Generate Gmail App Password](https://myaccount.google.com/apppasswords)
     
         **Steps:**
         1. Enable 2-Step Verification: [https://myaccount.google.com/security](https://myaccount.google.com/security)
         2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
         3. Select **Mail** as the app and **Other** as the device (enter "ATE Tool")
         4. Copy the 16-character password shown
     
         Paste that below along with your Gmail address.
         """)
   
        with st.form("email_form"):
           from_email = st.text_input("Your Gmail Address", placeholder="you@gmail.com")
           app_password = st.text_input("Your Gmail App Password", type="password", placeholder="16-character app password")
           to_email = st.text_input("Recipient Email", value="support@example.com")
           subject = st.text_input("Subject", value=f"Predictive Maintenance Alert - {selected_machine}")
           body = st.text_area("Message")
   
           send_button = st.form_submit_button("📤 Send Email")
   
           if send_button:
               if not all([from_email.strip(), app_password.strip(), to_email.strip(), subject.strip(), body.strip()]):
                   st.error("❌ Please fill in all fields.")
               else:
                   # Send email using user-provided credentials
                   try:
                       msg = EmailMessage()
                       msg.set_content(body)
                       msg["Subject"] = subject
                       msg["From"] = from_email
                       msg["To"] = to_email
   
                       with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                           smtp.login(from_email, app_password)
                           smtp.send_message(msg)
   
                       st.success("✅ Email sent successfully!")
                   except Exception as e:
                       st.error(f"❌ Failed to send email: {e}")
    

if __name__ == "__main__":
    main()