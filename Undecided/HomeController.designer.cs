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
	[Register("HomeController")]
	partial class HomeController
	{
		[Outlet]
		[GeneratedCode("iOS Designer", "1.0")]
		UIKit.UILabel lblWelcome { get; set; }

		void ReleaseDesignerOutlets()
		{
			if (lblWelcome != null)
			{
				lblWelcome.Dispose();
				lblWelcome = null;
			}
		}
	}
}