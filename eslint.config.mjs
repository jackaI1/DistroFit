import tseslint from "typescript-eslint";
export default tseslint.config(...tseslint.configs.recommended, {
  files: ["automation/office-script/clean.ts"],
  rules: { "@typescript-eslint/no-unused-vars": ["error", { varsIgnorePattern: "^main$" }] }
});
