# uwp-dp-boilerplate

## Copy from remote

### Hard copy (overwrites all local files)

Copy past this command into root of a dataproduct it will copy all boilerplate code into dataprodcut.

Warining it will override local files

```bash
t=$(mktemp -d) && git clone --depth=5 https://github.com/cultuurnet/uwp-dp-boilerplate "$t" 2>/dev/null && find "$t" -not -path "$t/.git*" -type f | while IFS= read -r f; do r="${f#$t/}"; mkdir -p "$(dirname "./$r")"; cp "$f" "./$r"; done; rm -rf "$t"
```

### Safe copy with diff comparison (Linux / WSL)

Shows a colored diff for changed files and asks to overwrite or skip. Identical files are skipped automatically.

This will not override local files but show diff and ask for confirmation.

```bash
#!/bin/bash
t=$(mktemp -d)
git clone --depth=5 https://github.com/cultuurnet/uwp-dp-boilerplate "$t" 2>/dev/null
find "$t" -not -path "$t/.git*" -type f | while IFS= read -r f; do
  r="${f#$t/}"
  dest="./$r"
  if [ ! -e "$dest" ]; then
    mkdir -p "$(dirname "$dest")"
    cp "$f" "$dest"
    echo "Copied: $r"
  elif diff -q "$f" "$dest" >/dev/null 2>&1; then
    :
  else
    echo ""
    echo -e "\033[1;34m╔══ $r ══\033[0m"
    diff --unified=2 "$dest" "$f" | tail -n +3 | while IFS= read -r line; do
      case "${line:0:1}" in
        +) echo -e "\033[32m$line\033[0m" ;;
        -) echo -e "\033[31m$line\033[0m" ;;
        @) echo -e "\033[36m$line\033[0m" ;;
        *) echo "  $line" ;;
      esac
    done
    echo -e "\033[1;34m╚══════\033[0m"
    read -rp "Overwrite $r? [y/n] " ans </dev/tty
    if [ "$ans" = "y" ]; then
      cp "$f" "$dest"
      echo "Overwritten: $r"
    else
      echo "Skipped: $r"
    fi
  fi
done
rm -rf "$t"
```

### Hard copy (overwrites all local files)

```bash
t=$(mktemp -d) && git clone --depth=5 https://github.com/cultuurnet/uwp-dp-boilerplate "$t" 2>/dev/null && find "$t" -not -path "$t/.git*" -type f | while IFS= read -r f; do r="${f#$t/}"; mkdir -p "$(dirname "./$r")"; cp "$f" "./$r"; done; rm -rf "$t"
```
