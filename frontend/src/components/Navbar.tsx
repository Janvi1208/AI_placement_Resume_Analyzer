import Link from "next/link";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Placement<span className="text-brand-500">AI</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-medium text-gray-600 md:flex">
          <Link href="/#how-it-works" className="hover:text-gray-900">How it works</Link>
          <Link href="/#features" className="hover:text-gray-900">Features</Link>
          <Link href="/profile" className="hover:text-gray-900">Profile</Link>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/profile" className="text-sm font-medium text-gray-700 hover:text-gray-900">
            Profile
          </Link>
          <Link href="/login" className="text-sm font-medium text-gray-700 hover:text-gray-900">
            Log in
          </Link>
          <Link href="/signup" className="btn-primary !px-4 !py-2 text-sm">
            Start Analyzing
          </Link>
        </div>
      </div>
    </header>
  );
}
