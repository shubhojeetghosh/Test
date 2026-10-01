from backend.authentication.core.email import send_otp_email


# ============================================================
# CHANGE THIS TO THE EMAIL WHERE YOU WANT TO RECEIVE OTP
# ============================================================

TEST_EMAIL = "aksbhgt@gmail.com"

TEST_OTP = "483821"


def main() -> None:
    """Send a manual OTP email only when this file is run directly."""
    print()
    print("========================================")
    print("TESTING OTP EMAIL")
    print("========================================")
    print()

    result = send_otp_email(
        to_email=TEST_EMAIL,
        otp=TEST_OTP
    )

    print()

    if result:
        print("========================================")
        print("SUCCESS")
        print("OTP email was sent.")
        print("Check Inbox and Spam.")
        print("========================================")
    else:
        print("========================================")
        print("FAILED")
        print("OTP email was NOT sent.")
        print("Read the error above.")
        print("========================================")


if __name__ == "__main__":
    main()
