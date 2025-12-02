import pytest
from playwright.sync_api import expect
from e2e.mocks import inject_wallet_mock

# The hardcoded instructor address from auth.py
INSTRUCTOR_WALLET = '0xa8cA165C69d2d9f4842428e0ea51EF9881eC59A4'
STUDENT_WALLET = '0x1234567890123456789012345678901234567890'


def test_student_submission_flow(page, base_url):
    """
    1. Student visits portal
    2. Connects wallet (is really optional, but good for UI)
    3. fills form and uploads file
    4. Submits claim
    """
    # 1. Inject Student Wallet
    inject_wallet_mock(page, STUDENT_WALLET)

    # 2. go to Student Portal
    page.goto(f"{base_url}/student/portal")
    expect(page).to_have_title("Student Portal - Blockchain Credentials")

    # 3. Fill the Form with random details in this test
    page.fill('input[name="student_name"]', "John Playwright")
    page.fill('input[name="student_email"]', "john@example.com")
    page.select_option('select[name="credential_type"]', "course-completion")
    page.fill('input[name="course_code"]', "CS101")
    page.fill('textarea[name="description"]', "E2E Test Description")

    # 4. Handle File Upload (Create a dummy file on the fly)
    # Note: We click the hidden input or the label trigger depending on implementation. Using specific handling for hidden input if standard click fails
    with page.expect_file_chooser() as fc_info:
        page.locator("#uploadZone").click()         #upload zone

    file_chooser = fc_info.value

    # dummy evidence file
    file_name = "test_evidence.txt"
    with open(file_name, "w") as f:
        f.write("This is dummy evidence content.")

    file_chooser.set_files(file_name)

    page.click('button[type="submit"]')

    # 6. Verify Success
    success_alert = page.locator(".alert-success")
    expect(success_alert).to_be_visible()
    expect(success_alert).to_contain_text("Claim submitted successfully")

    import os
    if os.path.exists(file_name):
        os.remove(file_name)


def test_instructor_approval_flow(page, base_url):
    """
    Prerequisite: Run after student submission
    1. Login as Instructor
    2. View Dashboard
    3. Approve Claim
    """
    # --- Quick Submit Setup (Seeding Data) ---
    page.goto(f"{base_url}/student/portal")
    page.fill('input[name="student_name"]', "Jane Doe")
    page.fill('input[name="student_email"]', "jane@example.com")
    page.select_option('select[name="credential_type"]', "diploma")
    page.fill('input[name="course_code"]', "SW202")
    page.click('button[type="submit"]')
    # --------------------------

    # 1. Inject Instructor Wallet
    inject_wallet_mock(page, INSTRUCTOR_WALLET)

    # 2. Login (This establishes the session cookie!)
    page.goto(f"{base_url}/")
    page.click("#connectWalletBtn")

    # Wait for redirect to dashboard
    page.wait_for_url(f"{base_url}/instructor/dashboard")
    expect(page.locator("h2")).to_contain_text("Instructor Dashboard")

    # 3. Find the claim in the table
    row = page.locator("tr", has_text="SW202")
    expect(row).to_be_visible()

    # 4. Click Approve
    page.on("dialog", lambda dialog: dialog.accept())
    row.locator(".btn-success").click()

    # 5. Verify Toast Success
    toast = page.locator(".toast-body")
    expect(toast).to_be_visible()
    expect(toast).to_contain_text("Claim approved")


def test_verification_flow(page, base_url):
    """
    1. Connect Student Wallet & Submit a claim
    2. Approve it (Mint it)
    3. Verify it on the public page
    """
    # 1. Login as Student (CRITICAL STEP ADDED)
    inject_wallet_mock(page, STUDENT_WALLET)
    page.goto(f"{base_url}/student/portal")
    page.click("#connectWalletBtn")

    # Verify wallet connected before filling form
    expect(page.locator("#connectWalletBtn")).to_contain_text("0x1234...7890")

    # 2. Fill & Submit Claim
    page.fill('input[name="student_name"]', "Verify Me")
    page.fill('input[name="student_email"]', "verify@me.com")
    page.select_option('select[name="credential_type"]', "micro-credential")

    # a unique course code to avoid "strict mode" errors with old data
    import time
    unique_code = f"VERIFY{int(time.time())}"
    page.fill('input[name="course_code"]', unique_code)

    page.click('button[type="submit"]')

    # 3. Login as Instructor
    # must re-inject because navigating can sometimes reset the window object
    inject_wallet_mock(page, INSTRUCTOR_WALLET)
    page.goto(f"{base_url}/")
    page.click("#connectWalletBtn")

    # 4. Wait for Dashboard and Approve
    page.wait_for_url(f"{base_url}/instructor/dashboard")

    # Handle the alert confirmation
    page.on("dialog", lambda dialog: dialog.accept())

    # Find row with our UNIQUE code and click approve i use .first just in case, but unique_code prevents duplicates
    row = page.locator("tr", has_text=unique_code)
    row.locator(".btn-success").first.click()

    # Wait for the toast saying "Minted" or "Approved"
    page.wait_for_timeout(2000)

    page.goto(f"{base_url}/verify/")

    # 6. Search. the MockBlockchainService in the conftest.py file returns id 999 for ALL mints, this is on purpose, line 22
    page.fill("#tokenInput", "999")
    page.click('button[type="submit"]')

    expect(page.locator("h4")).to_contain_text("Verified Credential")

    # check for the unique code we just created to ensure we loaded the right DB record
    expect(page.locator("body")).to_contain_text(unique_code)
    expect(page.locator(".badge.bg-light.text-dark")).to_contain_text("VALID")