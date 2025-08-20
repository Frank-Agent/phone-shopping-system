import UIKit
import WebKit

class ViewController: UIViewController {
    
    @IBOutlet weak var webView: WKWebView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        print("ViewController: viewDidLoad called")
        print("ViewController: View frame: \(view.frame)")
        
        view.backgroundColor = .systemBackground
        
        print("ViewController: viewDidLoad complete")
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        print("ViewController: viewWillAppear - View frame: \(view.frame)")
    }
    
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        print("ViewController: viewDidAppear - View frame: \(view.frame)")
        
        // Setup WebView after view is properly laid out
        if webView == nil {
            setupWebView()
            loadLoginPage()
        }
        
        print("ViewController: viewDidAppear - WebView frame: \(webView?.frame ?? .zero)")
        print("ViewController: viewDidAppear - WebView superview: \(webView?.superview != nil)")
    }
    
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        print("ViewController: viewDidLayoutSubviews - View frame: \(view.frame)")
        if let webView = webView {
            webView.frame = view.bounds
            print("ViewController: Updated WebView frame to: \(webView.frame)")
        }
    }
    
    private func setupWebView() {
        print("ViewController: setupWebView called")
        print("ViewController: Creating WKWebView with frame: \(view.bounds)")
        
        let webConfiguration = WKWebViewConfiguration()
        webConfiguration.preferences.javaScriptEnabled = true
        
        webView = WKWebView(frame: view.bounds, configuration: webConfiguration)
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        webView.navigationDelegate = self
        webView.backgroundColor = .white
        
        view.addSubview(webView)
        print("ViewController: WKWebView added to view with frame: \(webView.frame)")
    }
    
    private func loadLoginPage() {
        print("ViewController: loadLoginPage called")
        let htmlString = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login Test</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .login-container {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    width: 100%;
                    max-width: 400px;
                }
                
                .login-header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .login-header h1 {
                    color: #333;
                    margin: 0 0 10px 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                
                .login-header p {
                    color: #666;
                    margin: 0;
                    font-size: 16px;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                label {
                    display: block;
                    margin-bottom: 8px;
                    color: #333;
                    font-weight: 500;
                    font-size: 14px;
                }
                
                input[type="email"],
                input[type="password"] {
                    width: 100%;
                    padding: 12px 16px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 16px;
                    transition: border-color 0.3s ease;
                    box-sizing: border-box;
                    -webkit-appearance: none;
                }
                
                input[type="email"]:focus,
                input[type="password"]:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }
                
                .login-button {
                    width: 100%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 14px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s ease;
                }
                
                .login-button:hover {
                    transform: translateY(-1px);
                }
                
                .login-button:active {
                    transform: translateY(0);
                }
                
                .demo-credentials {
                    margin-top: 20px;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }
                
                .demo-credentials h3 {
                    margin: 0 0 10px 0;
                    color: #333;
                    font-size: 14px;
                }
                
                .demo-credentials p {
                    margin: 5px 0;
                    font-size: 13px;
                    color: #666;
                }
                
                .result {
                    margin-top: 20px;
                    padding: 15px;
                    border-radius: 8px;
                    display: none;
                }
                
                .result.success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .result.error {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="login-header">
                    <h1>Password Autofill Test</h1>
                    <p>Test iOS password autofill functionality</p>
                </div>
                
                <form id="loginForm" autocomplete="on">
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            autocomplete="username"
                            placeholder="Enter your email"
                            required
                        >
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            autocomplete="current-password"
                            placeholder="Enter your password"
                            required
                        >
                    </div>
                    
                    <button type="submit" class="login-button">Sign In</button>
                </form>
                
                <div class="demo-credentials">
                    <h3>Demo Credentials:</h3>
                    <p><strong>Email:</strong> demo@example.com</p>
                    <p><strong>Password:</strong> demo123456</p>
                    <p><em>Use these to test autofill after saving</em></p>
                </div>
                
                <div id="result" class="result"></div>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const resultDiv = document.getElementById('result');
                    
                    // Simple demo validation
                    if (email === 'demo@example.com' && password === 'demo123456') {
                        resultDiv.className = 'result success';
                        resultDiv.textContent = '✅ Login successful! Autofill is working properly.';
                        resultDiv.style.display = 'block';
                        
                        // Simulate redirect after successful login
                        setTimeout(() => {
                            resultDiv.textContent += ' (This would normally redirect to the app)';
                        }, 1000);
                    } else if (email && password) {
                        resultDiv.className = 'result error';
                        resultDiv.textContent = '❌ Invalid credentials. Try the demo credentials above.';
                        resultDiv.style.display = 'block';
                    } else {
                        resultDiv.className = 'result error';
                        resultDiv.textContent = '❌ Please fill in both email and password.';
                        resultDiv.style.display = 'block';
                    }
                    
                    // Clear result after 5 seconds
                    setTimeout(() => {
                        resultDiv.style.display = 'none';
                    }, 5000);
                });
                
                // Clear result when user starts typing
                document.getElementById('email').addEventListener('input', clearResult);
                document.getElementById('password').addEventListener('input', clearResult);
                
                function clearResult() {
                    document.getElementById('result').style.display = 'none';
                }
            </script>
        </body>
        </html>
        """
        
        print("ViewController: Loading HTML content")
        webView.loadHTMLString(htmlString, baseURL: nil)
        print("ViewController: HTML load initiated")
    }
}

extension ViewController: WKNavigationDelegate {
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        print("WebView finished loading")
        
        // Auto-fill the login form and submit
        performAutomatedLogin()
    }
    
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        print("WebView failed to load: \(error.localizedDescription)")
    }
    
    private func performAutomatedLogin() {
        print("Performing automated login...")
        
        // JavaScript to fill in the form fields and submit
        let jsScript = """
            // Wait a moment for the page to be fully ready
            setTimeout(function() {
                // Fill in the email field
                var emailField = document.getElementById('email');
                if (emailField) {
                    emailField.value = 'demo@example.com';
                    emailField.dispatchEvent(new Event('input', { bubbles: true }));
                    console.log('Email field filled');
                }
                
                // Fill in the password field
                var passwordField = document.getElementById('password');
                if (passwordField) {
                    passwordField.value = 'demo123456';
                    passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                    console.log('Password field filled');
                }
                
                // Click the login button after a brief delay
                setTimeout(function() {
                    var loginForm = document.getElementById('loginForm');
                    if (loginForm) {
                        loginForm.dispatchEvent(new Event('submit', { cancelable: true }));
                        console.log('Form submitted');
                    } else {
                        console.log('Login form not found');
                    }
                }, 500);
            }, 1000);
        """
        
        webView.evaluateJavaScript(jsScript) { result, error in
            if let error = error {
                print("JavaScript execution error: \(error.localizedDescription)")
            } else {
                print("Automated login script executed successfully")
            }
        }
    }
}
