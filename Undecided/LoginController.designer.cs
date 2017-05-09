// WARNING
//
// This file has been generated automatically by Xamarin Studio from the outlets and
// actions declared in your storyboard file.
// Manual changes to this file will not be maintained.
//
using Foundation;
using System;
using System.CodeDom.Compiler;
using UIKit;

namespace Undecided
{
	[Register("LoginController")]
	partial class LoginController
	{
		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UIButton btnLogin { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UIButton btnSignUp { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtEmail { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtPassword { get; set; }

		[Action("BtnLogin_TouchUpInside:")]
		[GeneratedCode("iOS Designer", "1.0")]
		partial void BtnLogin_TouchUpInside(UIKit.UIButton sender);

		void ReleaseDesignerOutlets()
		{
			if (btnLogin != null)
			{
				btnLogin.Dispose();
				btnLogin = null;
			}

			if (btnSignUp != null)
			{
				btnSignUp.Dispose();
				btnSignUp = null;
			}

			if (txtEmail != null)
			{
				txtEmail.Dispose();
				txtEmail = null;
			}

			if (txtPassword != null)
			{
				txtPassword.Dispose();
				txtPassword = null;
			}
		}
	}
}