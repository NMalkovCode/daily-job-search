# CV files

Put your CV files in this folder. **They are git-ignored**: only this README is ever committed.

Then list them in `config/settings.json → candidate.cvs`, as `id → file name`:

```json
"cvs": {
  "general": "My CV.pdf",
  "technical": "My CV Technical.pdf"
}
```

- The ids (`general`, `technical`, …) are what Claude writes in each pick. Use as many CVs as you
  like, or just one.
- Describe when to use each one in `config/profile.md → Fields to write per job → cv`.
- Sub-folders are fine: `"finance": "Finance/My CV Finance.pdf"`.
- Your CVs can also stay where they are: set `candidate.cv_root` to that folder, e.g.
  `"C:/Users/you/Documents/CVs"` (use forward slashes).

Check with `python -m jobsearch doctor` (see the main README for the exact command on your
system). The tracker's "CV to send" column links straight to the file.
