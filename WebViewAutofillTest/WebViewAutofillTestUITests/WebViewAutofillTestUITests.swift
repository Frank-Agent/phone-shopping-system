//
//  WebViewAutofillTestUITests.swift
//  WebViewAutofillTestUITests
//
//  Created by Ofer Samocha on 19/08/2025.
//

import XCTest

final class WebViewAutofillTestUITests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.

        // In UI tests it is usually best to stop immediately when a failure occurs.
        continueAfterFailure = false

        // In UI tests it’s important to set the initial state - such as interface orientation - required for your tests before they run. The setUp method is a good place to do this.
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
    }

    func testExample() throws {
        // UI tests must launch the application that they test.
        let app = XCUIApplication()
        app.launch()

        // Use XCTAssert and related functions to verify your tests produce the correct results.
    }
    
    func testWebViewLoginAutomation() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Wait for the web view to load
        let webView = app.webViews.firstMatch
        XCTAssertTrue(webView.waitForExistence(timeout: 5), "WebView should exist")
        
        // Find and fill the email field
        let emailField = webView.textFields["email"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 3), "Email field should exist")
        emailField.tap()
        emailField.typeText("demo@example.com")
        
        // Find and fill the password field
        let passwordField = webView.secureTextFields["password"]
        XCTAssertTrue(passwordField.waitForExistence(timeout: 3), "Password field should exist")
        passwordField.tap()
        passwordField.typeText("demo123456")
        
        // Find and click the login button
        let loginButton = webView.buttons["Sign In"]
        XCTAssertTrue(loginButton.waitForExistence(timeout: 3), "Login button should exist")
        loginButton.tap()
        
        // Verify successful login message appears
        let successMessage = webView.staticTexts.containing(NSPredicate(format: "label CONTAINS[c] 'Login successful'")).firstMatch
        XCTAssertTrue(successMessage.waitForExistence(timeout: 5), "Success message should appear after login")
    }

    func testLaunchPerformance() throws {
        if #available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 7.0, *) {
            // This measures how long it takes to launch your application.
            measure(metrics: [XCTApplicationLaunchMetric()]) {
                XCUIApplication().launch()
            }
        }
    }
}
