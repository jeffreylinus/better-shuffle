function Login() {
    return (
        <button onClick={() => {
            window.location.href = "/api/auth";
        }}>
            Connect to Spotify
        </button>
    );
}

export default Login;