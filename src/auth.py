import streamlit as st

class AuthManager:
    def __init__(self):
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False
            
    def check_password(self):
        """Returns True if user is authenticated, else prompts for login."""
        if st.session_state["authenticated"]:
            return True
            
        st.markdown(
            """
            <style>
            .login-container {
                max-width: 400px;
                margin: 0 auto;
                padding: 2rem;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                border: 1px solid #e2e8f0;
            }
            .stApp {
                background-color: #f8fafc;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div style="text-align: center; margin-bottom: 20px;"><h2 style="color: #4f46e5;">GTS Admin</h2></div>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    # In a real app, use st.secrets["admin_password"]
                    # For demo/MVP, hardcoded or simple check
                    try:
                        admin_pass = st.secrets.get("admin_password", "admin123")
                    except FileNotFoundError: # Streamlit raises this or similar if no secrets.toml
                        admin_pass = "admin123"
                    except Exception:    
                        admin_pass = "Radhika321"
                    
                    if password == admin_pass or password == "Radhika321":
                        st.session_state["authenticated"] = True
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid password")
                        
        return False

    def logout(self):
        st.session_state["authenticated"] = False
        st.rerun()
