# shici demo recording — VHS script
#
# This script generates a GIF that demonstrates shici in action.
# Run with:  vhs scripts/demo.tape
# Output goes to docs/assets/demo.gif

Output docs/assets/demo.gif

Set FontSize 14
Set Width 1200
Set Height 720
Set Padding 20
Set Theme "Catppuccin Mocha"

# Show welcome
Type "shici --version"
Sleep 500ms
Enter
Sleep 1500ms

Type "shici check examples/jueju-5.txt"
Sleep 500ms
Enter
Sleep 3000ms

# Move to next command
Type "shici duilian \"天增岁月人增寿\" \"春满乾坤福满门\""
Sleep 500ms
Enter
Sleep 3000ms

Type "shici cipai"
Sleep 500ms
Enter
Sleep 3000ms

Type "shici lint \"床前明月光\""
Sleep 500ms
Enter
Sleep 3000ms

Type "shici rhyme 光"
Sleep 500ms
Enter
Sleep 2500ms