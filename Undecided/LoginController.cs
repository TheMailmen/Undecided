using Foundation;
using System;
using UIKit;
using Parse;

namespace Undecided
{
    public partial class LoginController : UIViewController
    {
	
		public LoginController (IntPtr handle) : base (handle)
        {
        }

		public override void ViewDidLoad()
		{
			if (ParseUser.CurrentUser != null)
			{
				// navigate to the welcome page, 
				var home = Storyboard.InstantiateViewController("home") as HomeController;
				NavigationController.PushViewController(home, true);
			}
		}

		async partial void BtnLogin_TouchUpInside(UIButton sender)
		{
			// to prevent the user from clicking on the button multiple times, 
			// I will hide my login button when it is clicked on till all the processing is complete
			btnLogin.Hidden = true;
			var email = txtEmail.Text;
			var password = txtPassword.Text;
			var error = "Enter a valid E-mail Address and Password";

			var alert = new UIAlertView();

			// if email and password is not provided don't make the Parse call
			if ((string.IsNullOrEmpty(email)) || (string.IsNullOrEmpty(password)))
			{
				alert = new UIAlertView("Login Failed", error, null, "OK");
				alert.Show();
			}
			else
			{
				try
				{
					// you only need this one line to authenticate the user against Parse
					ParseUser myUser = await ParseUser.LogInAsync(email, password);

					// navigate to the welcome page, 
					// note: "home" is the StoryBoard ID of the HomeController
					var home = Storyboard.InstantiateViewController("home") as HomeController;
					NavigationController.PushViewController(home, true);
				}
				catch (ParseException f)
				{
					alert = new UIAlertView("Login Failed", error, null, "OK");
					alert.Show();
				}
				catch (Exception f)
				{
					alert = new UIAlertView("Login Failed",
								   "Check your network access! Or try again later", null, "OK");
					alert.Show();
				}
			}
			// now I will display my login button
			btnLogin.Hidden = false;
		}

    }
}