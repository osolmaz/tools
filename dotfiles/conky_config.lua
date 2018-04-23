
conky.config={
   --  Create own window instead of using desktop (required in nautilus)
   own_window=true,
   own_window_hints="undecorated,below,sticky,skip_taskbar,skip_pager",
   own_window_type="override",
   own_window_colour="brown",
   own_window_transparent=true,
   background=true,
   --  Use double buffering (reduces flicker, may not work for everyone)
   double_buffer=true,
   --  fiddle with window
   use_spacer="right",
   use_xft=true,
   --  Update interval in seconds
   update_interval=3,
   --  Minimum size of text area
   --  minimum_size 400 5
   --  maximum_width 400
   --  Draw shades?
   draw_shades=true,
   --  Text stuff
   draw_outline=false, --  amplifies text if yes
   draw_borders=false,
   uppercase=false, --  set to yes if you want all text to be in uppercase
   --  Stippled borders?
   stippled_borders=8,
   --  border margins
   border_inner_margin=4,
   border_outer_margin=0,
   --  border width
   border_width=1,
   --  Default colors and also border colors, grey90 == -- e5e5e5
   default_color="white",
   default_shade_color="black",
   default_outline_color="white",
   --
   --  Text alignment, other possible values are commented
   -- alignment top_left
   -- alignment top_right
   --  alignment middle_left
   alignment="top_left",
   -- alignment bottom_left
   -- alignment bottom_right
   --  Gap between borders of screen and text
   gap_x=100,
   gap_y=100,
   --  stuff after 'TEXT' will be formatted on screen
   -- override_utf8_locale no
   --  xftfont Consolas:size=11:style:bold
   --  xftfont Dejavu Sans Mono:size=12:style:bold
   -- xftfont Open Sans:size=8 style:bold
   font="Consolas:size=11:style:bold",
   --
}
conky.text = [[
${color slate grey}${time %a,  } ${color }${time %e %B %G}
${color slate grey}${time %Z,    }${color }${time %H:%M:%S}
${color slate grey}UpTime: ${color }$uptime
${color slate grey}Kern:   ${color }$kernel
${color slate grey}CPU:    ${color } $cpu%  ${color red} ${acpitemp} ${color }crit ${color red}89${color }
${color slate grey}ctemp:  ${color } ${color red}${platform coretemp.0 temp 2}${color}, ${color red}${platform coretemp.0 temp 4}${color} crit ${color red}90${color}
${cpugraph 40,180 000000 ffffff}
${color slate grey}Load: ${color }$loadavg
${color slate grey}Processes: ${color }$processes
${color slate grey}Running:   ${color }$running_processes

${color slate grey}Highest CPU:
${color #ddaa00} ${top name 1}${top_mem cpu 1}
${color lightgrey} ${top name 2}${top cpu 2}
${color lightgrey} ${top name 3}${top cpu 3}
${color lightgrey} ${top name 4}${top cpu 4}
${color lightgrey} ${top name 5}${top cpu 5}

${color slate grey}Highest MEM:
${color #ddaa00} ${top_mem name 1}${top_mem mem 1}
${color lightgrey} ${top_mem name 2}${top_mem mem 2}
${color lightgrey} ${top_mem name 3}${top_mem mem 3}
${color lightgrey} ${top_mem name 4}${top_mem mem 4}
${color lightgrey} ${top_mem name 5}${top_mem mem 5}

${color slate grey}MEM:  ${color } $memperc% $mem/$memmax
${membar 5,180}
${color slate grey}SWAP: ${color }$swapperc% $swap/$swapmax
${swapbar 5,180}
${color slate grey}ROOT:    ${color }${fs_free /}/${fs_size /}
${fs_bar 5,180 /}
${color slate grey}HOME:  ${color }${fs_free /home}/${fs_size /home}
${fs_bar 5,180 /home}
${color slate grey}NET:
${color}Up: ${color }${upspeed eth0} k/s
${upspeedgraph eth0 40,180 000000 ffffff}
${color}Down: ${color }${downspeed eth0}k/s${color}
${downspeedgraph eth0 40,180 000000 ffffff}
]]
