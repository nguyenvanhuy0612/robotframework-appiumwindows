
remote_path = "C:\\Users\\admin\\Documents\\test.txt"
remote_b64_path = "C:\\Users\\admin\\Documents\\test.txt.b64"
decode_script = (
    f'[IO.File]::WriteAllBytes("{remote_path}", '
    f'[Convert]::FromBase64String((Get-Content "{remote_b64_path}" -Raw)))'
)

print(decode_script)
