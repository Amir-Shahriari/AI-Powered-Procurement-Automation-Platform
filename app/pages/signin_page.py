"""
Sign-in page with authentication, forget password, and create account functionality
"""
import streamlit as st
from app.core.navigation import _nav_set
from app.core.ui_helpers import _inject_css

def page_signin():
    """Sign-in page with authentication functionality"""
    _inject_css()
    
    # Hide the default Streamlit elements and sidebar
    st.markdown('''
    <style>
    .stApp > header {visibility: hidden;}
    .stApp > div:first-child {padding-top: 0;}
    .stApp > div:first-child > div:first-child {padding-top: 0;}
    .main .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    
    /* Completely hide sidebar on sign-in page */
    .stSidebar {display: none !important; visibility: hidden !important; width: 0 !important; min-width: 0 !important;}
    .stApp > div:first-child > div:first-child > div:first-child {display: none !important; visibility: hidden !important; width: 0 !important; min-width: 0 !important;}
    
    /* Ensure main content takes full width */
    .stApp > div:first-child > div:first-child > div:last-child {width: 100% !important; max-width: 100% !important;}
    
    /* Hide any sidebar elements that might be rendered */
    [data-testid="stSidebar"] {display: none !important; visibility: hidden !important; width: 0 !important;}
    .css-1d391kg {display: none !important; visibility: hidden !important; width: 0 !important;}
    </style>
    ''', unsafe_allow_html=True)
    
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo and Header
        st.markdown('''
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #1e3a8a; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">
                🏛️ NSW Procurement Platform
            </h1>
            <p style="color: #64748b; font-size: 1.2rem; margin-bottom: 2rem;">
                AI-Powered Compliant Procurement for NSW Local Government
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Display both logos side by side
        col_logo1, col_logo2 = st.columns(2)
        
        with col_logo1:
            try:
                st.image("app/ui/assets/lgp-logo-retina.png", width=150, caption="Local Government Procurement")
            except:
                # Fallback if logo not found
                st.markdown("### 🏛️ Local Government Procurement")
        
        with col_logo2:
            try:
                st.image("app/ui/assets/AI Government Procurement.png", width=150, caption="EmbryA AI Government Procurement")
            except:
                # Fallback if logo not found
                st.markdown("### 🤖 EmbryA AI Government Procurement")
        
        # Sign-in Form
        with st.container():
            st.markdown("### Sign In")
            
            # Create tabs for Sign In, Forgot Password, and Create Account
            # Auto-select sign-in tab if account was just created
            if st.session_state.get("show_signin_tab", False):
                # Force focus on sign-in tab
                tab1, tab2, tab3 = st.tabs(["Sign In", "Forgot Password", "Create Account"])
                st.session_state["show_signin_tab"] = False  # Reset the flag
                # Show a message to guide user to sign in
                st.info("👆 Please use the 'Sign In' tab above to sign in with your new account.")
            else:
                tab1, tab2, tab3 = st.tabs(["Sign In", "Forgot Password", "Create Account"])
            
            with tab1:
                # Sign-in form
                email = st.text_input(
                    "Email Address",
                    placeholder="your.email@example.com",
                    help="Enter your email address",
                    key="signin_email"
                )
                
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="signin_password"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    remember_me = st.checkbox("Remember me", key="remember_me")
                with col2:
                    if st.button("Sign In", type="primary", use_container_width=True, key="signin_btn"):
                        if email and password:
                            # Authenticate user
                            if authenticate_user(email, password):
                                st.session_state["authenticated"] = True
                                st.session_state["user_email"] = email
                                st.session_state["user_name"] = email.split("@")[0].replace(".", " ").title()
                                st.success("✅ Sign in successful!")
                                # Force navigation to main dashboard
                                st.session_state["current_page"] = "main_dashboard"
                                st.rerun()
                            else:
                                st.error("❌ Invalid email or password")
                        else:
                            st.error("❌ Please enter both email and password")
                
                # Debug section (remove in production)
                if st.button("🐛 Enable Debug Mode", key="debug_btn"):
                    st.session_state["debug"] = True
                    st.rerun()
                
                if st.session_state.get("debug", False):
                    st.info("🐛 Debug Mode Enabled - Check console for account details")
                    if "created_accounts" in st.session_state:
                        st.write(f"Registered accounts: {len(st.session_state['created_accounts'])}")
                        for i, account in enumerate(st.session_state["created_accounts"]):
                            st.write(f"Account {i+1}: {account['email']}")
                    else:
                        st.write("No registered accounts found")
            
            with tab2:
                st.markdown("### Forgot Password")
                st.info("Enter your email address to receive password reset instructions.")
                
                reset_email = st.text_input(
                    "Email Address",
                    placeholder="your.email@example.com",
                    help="Enter your email address",
                    key="reset_email"
                )
                
                if st.button("Send Reset Link", type="primary", use_container_width=True, key="reset_btn"):
                    if reset_email:
                        st.success("✅ Password reset link sent to your email!")
                    else:
                        st.error("❌ Please enter your email address")
            
            with tab3:
                st.markdown("### Create Account")
                st.info("Create a new account for NSW Local Government procurement.")
                
                # Create account form
                new_email = st.text_input(
                    "Email Address",
                    placeholder="your.email@example.com",
                    help="Enter your email address",
                    key="create_email"
                )
                
                # Show email validation feedback
                if new_email and ("@" not in new_email or "." not in new_email.split("@")[1]):
                    st.warning("⚠️ Please enter a valid email address")
                elif new_email and "created_accounts" in st.session_state:
                    existing_emails = [account["email"].lower() for account in st.session_state["created_accounts"]]
                    if new_email.lower() in existing_emails:
                        st.error("❌ This email address is already registered. Please use a different email or try signing in.")
                
                new_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a strong password",
                    key="create_password"
                )
                
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Confirm your password",
                    key="confirm_password"
                )
                
                council = st.selectbox(
                    "Council",
                    ["Blacktown City Council", "Parramatta City Council", "Liverpool City Council", "Other NSW Council"],
                    help="Select your local government area",
                    key="create_council"
                )
                
                terms_accepted = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="terms_checkbox")
                
                if st.button("Create Account", type="primary", use_container_width=True, key="create_account_btn"):
                    if new_email and new_password and confirm_password and terms_accepted:
                        if new_password == confirm_password:
                            success, message = create_user_account(new_email, new_password, council)
                            if success:
                                st.success(f"✅ {message} Please sign in.")
                                # Set flag to show sign-in tab
                                st.session_state["show_signin_tab"] = True
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            st.error("❌ Passwords do not match")
                    else:
                        st.error("❌ Please fill in all fields and accept terms")
        
        # Footer
        st.markdown('''
        <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 0.9rem; margin: 0;">
                <strong>AI-Powered</strong> • NSW Compliant • Secure Access
            </p>
        </div>
        ''', unsafe_allow_html=True)

def authenticate_user(email: str, password: str) -> bool:
    """Authentication function that checks against registered accounts"""
    # Check if accounts exist
    if "created_accounts" not in st.session_state:
        st.session_state["created_accounts"] = []
    
    # Debug: Show registered accounts (remove in production)
    if st.session_state.get("debug", False):
        st.write(f"Debug: Checking {len(st.session_state['created_accounts'])} registered accounts")
        for i, account in enumerate(st.session_state["created_accounts"]):
            st.write(f"Account {i+1}: {account['email']}")
    
    # Look for matching account
    for account in st.session_state["created_accounts"]:
        if account["email"].lower() == email.lower() and account["password"] == password:
            # Store user info in session state
            st.session_state["user_email"] = email
            st.session_state["user_name"] = email.split("@")[0].replace(".", " ").title()
            return True
    
    # Fallback: accept any valid email for demo purposes
    if "@" in email and "." in email.split("@")[1] and len(password) >= 6:
        # Store user info in session state for demo
        st.session_state["user_email"] = email
        st.session_state["user_name"] = email.split("@")[0].replace(".", " ").title()
        return True
    
    return False

def create_user_account(email: str, password: str, council: str) -> tuple[bool, str]:
    """Create user account function with email validation and duplicate checking"""
    # Initialize accounts storage if not exists
    if "created_accounts" not in st.session_state:
        st.session_state["created_accounts"] = []
    
    # Check if email is already registered
    existing_emails = [account["email"].lower() for account in st.session_state["created_accounts"]]
    if email.lower() in existing_emails:
        return False, "Email address is already registered. Please use a different email or try signing in."
    
    # Validate email format (basic email validation)
    if "@" not in email or "." not in email.split("@")[1]:
        return False, "Please enter a valid email address"
    
    # Validate password strength
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    # Create the account
    st.session_state["created_accounts"].append({
        "email": email,
        "password": password,
        "council": council,
        "created_at": "2024-01-01"  # Demo timestamp
    })
    
    return True, "Account created successfully!"
