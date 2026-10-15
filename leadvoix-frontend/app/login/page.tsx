
import Link from "next/link";
import LoginForm from "@/modules/auth/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8">
      <header className="mx-auto mb-8 flex max-w-5xl items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-3"
          aria-label="LeadVoix home"
        >
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-xl font-bold text-white">
            L
          </span>

          <span className="text-2xl font-bold tracking-tight text-slate-900">
            LeadVoix
          </span>
        </Link>

        <Link
          href="/signup"
          className="text-sm font-semibold text-slate-700 hover:text-blue-600"
        >
          Sign up
        </Link>
      </header>

      <LoginForm />
    </main>
  );
}
