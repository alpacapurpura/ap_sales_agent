import { SignIn } from "@clerk/nextjs";

export default function Page() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100 dark:bg-slate-900">
      <SignIn 
        routing="path" 
        path="/sign-in" 
        signUpUrl="/sign-up"
        forceRedirectUrl="/"
      />
    </div>
  );
}
