import streamlit as st

css = """
    .st-key-green_container {
        background-color: rgba(100, 145, 100, 0.3); 
        border-radius: 20px; 
        padding: 20px; 
        max-width: 1000 rem;
    }
    .st-key-yellow_container {
        background-color: rgba(241, 194, 50, 0.3); 
        border-radius: 20px; 
        padding: 20px; 
        max-width: 1000 rem;
    }
    """

def home_page():
    st.set_page_config(
        page_title="Home",
    )

    with st.container(border = True, key = "green_container"):
        st.html(f"<style>{css}</style>")

        st.write("# Welcome to Streamlit! 👋")

        # st.sidebar.success("Select your choice to enter for a new Experiemnt or choose previous experiment")

        st.markdown(
            """
            Streamlit is an open-source app framework built specifically for
            Machine Learning and Data Science projects.
            **👈 Select a demo from the sidebar** to see some examples
            of what Streamlit can do!
            ### Want to learn more?
            - Check out [streamlit.io](https://streamlit.io)
            - Jump into our [documentation](https://docs.streamlit.io)
            - Ask a question in our [community
                forums](https://discuss.streamlit.io)
            ### See more complex demos
            - Use a neural net to [analyze the Udacity Self-driving Car Image
                Dataset](https://github.com/streamlit/demo-self-driving)
            - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
        """
        )