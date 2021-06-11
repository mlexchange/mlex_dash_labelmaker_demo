# Design Guide to the Dash App

The Dash app is organized as a multipage app. 
```
                   .--------.
                   | app.py |
                   '--------'
                        |
                        |
                        v
               .-----------------.
               |    index.py     |
               '-----------------'
                        |
                        |
                        |
                        v
         |------------------------------|
         |              |               |
         |              |               |
         v              |               v
  .-------------.       |     .------------------.
  | welcome.py  |       |     |   training.py    |
  '-------------'       v     '------------------'
              .------------------.
              | thumbnail_tab.py |
              '------------------'
```

The app.py initializes the dash app. Index.py organizes the multipage app. Welcome is a splash page (needs to be expanded to allow you to register sessions). Thumbnail_tab.py is where data is uploaded. Training.py is where the model training is launched from and displays results from this as well.
