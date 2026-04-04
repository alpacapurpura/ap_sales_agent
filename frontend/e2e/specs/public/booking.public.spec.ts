import { test, expect } from '@playwright/test';
import { BookingPage } from '../../pages/booking.page';

test.describe('Public Booking Pages', () => {
  test('booking page renders with valid slug', async ({ page }) => {
    const bookingPage = new BookingPage(page);
    await bookingPage.goto('test-booking');
    await bookingPage.expectLoaded();
  });
});
