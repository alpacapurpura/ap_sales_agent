import {
  GitFork,
  Database,
  Sparkles,
  User,
  Wrench,
  BrainCircuit,
  Activity,
  ShieldCheck,
  Zap,
  Network,
  Brain,
  LogIn,
  LogOut,
} from "lucide-react";

/**
 *
 */
export function getNodeIcon(nodeName: string | undefined, hasLLM = false) {
  if (hasLLM) return Brain;
  if (!nodeName) return BrainCircuit;

  const name = nodeName.toLowerCase();

  if (name.includes("__start__") || name.includes("entry")) return LogIn;
  if (name.includes("__end__") || name.includes("exit_point")) return LogOut;

  if (name.includes("router") || name.includes("decision")) return GitFork;
  if (name.includes("retrieve") || name.includes("search") || name.includes("knowledge"))
    return Database;
  if (name.includes("generate") || name.includes("llm") || name.includes("answer")) return Sparkles;
  if (name.includes("check") || name.includes("grade") || name.includes("validate"))
    return ShieldCheck;
  if (name.includes("human") || name.includes("user")) return User;
  if (name.includes("tool") || name.includes("function")) return Wrench;
  if (name.includes("classify")) return Network;
  if (name.includes("embed")) return Zap;

  return Activity;
}

/**
 *
 */
export function getNodeColor(nodeName: string | undefined) {
  if (!nodeName) return "text-slate-500";

  const name = nodeName.toLowerCase();

  if (name.includes("__start__") || name.includes("entry")) return "text-emerald-500";
  if (name.includes("__end__") || name.includes("exit_point")) return "text-emerald-500";

  if (name.includes("router")) return "text-blue-500";
  if (name.includes("retrieve")) return "text-orange-500";
  if (name.includes("generate")) return "text-purple-500";
  if (name.includes("check")) return "text-green-500";
  if (name.includes("error")) return "text-red-500";

  return "text-slate-500";
}
