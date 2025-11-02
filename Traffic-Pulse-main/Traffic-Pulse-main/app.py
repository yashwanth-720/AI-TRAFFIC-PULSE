import streamlit.web.cli as stcli
import sys

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "streamlit_app.py",
                "--server.port=7860", "--server.address=127.0.0.1"]
    sys.exit(stcli.main())
