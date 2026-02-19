import { Inter } from 'next/font/google';

import StoreWrapper from './storeWrapper.js';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Demo of lo_assess',
  description: 'By Piotr Mitros and Paul Deane',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <StoreWrapper>
        <body className={inter.className}>{children}</body>
      </StoreWrapper>
    </html>
  )
}
