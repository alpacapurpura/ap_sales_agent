
import { z } from "zod";

const emptyStringToNull = (val: unknown) => (val === "" ? null : val);

const Schema = z.object({
  start_date: z.preprocess(emptyStringToNull, z.string().datetime().optional().nullable()),
});

const test1 = Schema.safeParse({ start_date: "" });
console.log("Test 1 (empty string):", test1.success ? "Success" : test1.error);

const test2 = Schema.safeParse({ start_date: undefined });
console.log("Test 2 (undefined):", test2.success ? "Success" : test2.error);

const test3 = Schema.safeParse({ start_date: null });
console.log("Test 3 (null):", test3.success ? "Success" : test3.error);

const test4 = Schema.safeParse({ start_date: "invalid-date" });
console.log("Test 4 (invalid string):", test4.success ? "Success" : test4.error);
