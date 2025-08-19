import UIKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        print("SceneDelegate: willConnectTo called")
        guard let windowScene = (scene as? UIWindowScene) else { 
            print("SceneDelegate: Failed to get windowScene")
            return 
        }
        
        print("SceneDelegate: Creating window")
        window = UIWindow(windowScene: windowScene)
        
        print("SceneDelegate: Creating ViewController")
        let viewController = ViewController()
        window?.rootViewController = viewController
        
        print("SceneDelegate: Making window key and visible")
        window?.makeKeyAndVisible()
        
        print("SceneDelegate: Setup complete, window: \(String(describing: window))")
        print("SceneDelegate: Root VC: \(String(describing: window?.rootViewController))")
    }
}
