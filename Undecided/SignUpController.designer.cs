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
	[Register("SignUpController")]
	partial class SignUpController
	{
		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UIButton btnCreateAccount { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtConfirmPassword { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtEmail { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtFirstName { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtLastName { get; set; }

		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UITextField txtPassword { get; set; }

		[Action("BtnCreateAccount_TouchUpInside:")]
		[GeneratedCode("iOS Designer", "1.0")]
		partial void BtnCreateAccount_TouchUpInside(UIKit.UIButton sender);

		void ReleaseDesignerOutlets()
		{
			if (btnCreateAccount != null)
			{
				btnCreateAccount.Dispose();
				btnCreateAccount = null;
			}

			if (txtConfirmPassword != null)
			{
				txtConfirmPassword.Dispose();
				txtConfirmPassword = null;
			}

			if (txtEmail != null)
			{
				txtEmail.Dispose();
				txtEmail = null;
			}

			if (txtFirstName != null)
			{
				txtFirstName.Dispose();
				txtFirstName = null;
			}

			if (txtLastName != null)
			{
				txtLastName.Dispose();
				txtLastName = null;
			}

			if (txtPassword != null)
			{
				txtPassword.Dispose();
				txtPassword = null;
			}
		}
	}
}