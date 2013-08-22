describe '...'
  before
    new
    put =[
    \   'foo',
    \   'bar',
    \   'baz',
    \   '...',
    \ ]
  end

  after
    close!
  end

  it 'blub'
    Expect range(1) == [0]
  end

  it 'bla'
  end

  it 'ble'
  end
end

" vim: et:ts=2:sw=2
