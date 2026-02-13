import { SignUp } from "@clerk/nextjs";

export default function Page() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100 dark:bg-slate-900">
      <SignUp 
        routing="path" 
        path="/sign-up" 
        signInUrl="/sign-in"
        forceRedirectUrl="/"
      />
    </div>
  );
}
